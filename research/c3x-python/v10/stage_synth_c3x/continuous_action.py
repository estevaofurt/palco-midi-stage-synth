"""STAGE SYNTH C3X V10 - mecanismo de tecla continuo e escapamento por estados.

Este e um modelo REDUZIDO, nao a geometria real da acao Yamaha C3X.
Amostra a posicao da tecla e implementa regras de rearme de dupla repeticao.
Nao gera audio por amostras gravadas.
"""
from dataclasses import dataclass
import math
from collections import defaultdict
from .action import _hammer_speed, _velocity_from_speed


@dataclass(frozen=True)
class ContinuousActionConfig:
    key_dip_mm: float = 10.0           # referencial, NAO especificacao C3X
    escapement_key_fraction: float = .82
    double_reset_fraction: float = .54
    single_reset_fraction: float = .13
    key_speed_ratio: float = .32       # velocidade tecla / velocidade martelo
    key_release_speed_m_s: float = .47
    hammer_flight_mm: float = 1.7
    hammer_flight_drag_per_s: float = 3.
    backcheck_double_ms: float = 12.
    backcheck_single_ms: float = 35.
    felt_rate_exponent: float = .055
    simulation_hz: int = 2000
    damper_release_fraction: float = .22

    def validate(self):
        for v in vars(self).values():
            if not math.isfinite(float(v)):
                raise ValueError('Parametro nao finito da acao V10')
        if not (5<=self.key_dip_mm<=13 and .55<=self.escapement_key_fraction<=.95
                and 0<self.single_reset_fraction<self.double_reset_fraction<self.escapement_key_fraction
                and .05<=self.key_speed_ratio<=1.
                and .05<=self.key_release_speed_m_s<=2.
                and .3<=self.hammer_flight_mm<=5.
                and 0<=self.hammer_flight_drag_per_s<=30.
                and 2<=self.backcheck_double_ms<=self.backcheck_single_ms<=90
                and 0<=self.felt_rate_exponent<=.18
                and isinstance(self.simulation_hz,int) and 500<=self.simulation_hz<=10000
                and 0<self.damper_release_fraction<self.single_reset_fraction+.4):
            raise ValueError('Parâmetros de ação V10 fora da faixa experimental')
        return self


def _validated_events(events, length):
    validated=[]
    for e in events:
        if len(e)!=4 or not all(math.isfinite(float(z)) for z in e):
            raise ValueError('Evento de tecla invalido')
        t,n,hold,velocity=e
        if not (0<=t<length and 0<=hold<=length and int(n)==n and 21<=n<=108
                and int(velocity)==velocity and 1<=velocity<=127):
            raise ValueError('Evento de tecla fora da faixa')
        validated.append((float(t),int(n),float(hold),int(velocity)))
    return sorted(validated,key=lambda e:(e[0],e[1]))


def _to_keyframes(events,length):
    frames=[]
    for t,n,hold,vel in _validated_events(events,length):
        frames.append((t,n,1.,vel))
        if t+hold<length:frames.append((t+hold,n,0.,0))
    return frames


def schedule_continuous_action(events, length, keyframes=None, config=None,
                               mode='double', include_trajectories=False):
    """Converte comandos em colisões via curso continuo de tecla.

    events: (tempo, MIDI, duracao pressionada, intensidade)
    keyframes: (tempo, MIDI, profundidade [0,1], intensidade de DESCIDA)
      Quando keyframes e fornecido ele substitui eventos. Uma tecla pode
      descer parcialmente sem escapar. Profundidade menor que o limite de
      rearme, seguida de nova descida, pode produzir nova colisao.
    Saida: eventos audio (impacto_s,MIDI,duracao_s,velocidade MIDI),
    diagnostico com velocidade do martelo NAO quantizada e posicao de tecla.
    """
    cfg=(config or ContinuousActionConfig()).validate()
    if mode not in ('double','single'):raise ValueError('Modo de escapamento desconhecido')
    if not (math.isfinite(length) and 0<length<=60):raise ValueError('Duracao invalida')
    if keyframes is None:
        cmds=_to_keyframes(events,length)
    else:
        if events:raise ValueError('Use events OU keyframes para evitar ambiguidade')
        cmds=keyframes
    by_key=defaultdict(list)
    for c in cmds:
        if len(c)!=4 or not all(math.isfinite(float(v)) for v in c):
            raise ValueError('Keyframe invalido')
        t,n,depth,vel=c
        if not (0<=t<length and int(n)==n and 21<=n<=108 and 0<=depth<=1
                and int(vel)==vel and 0<=vel<=127):
            raise ValueError('Keyframe fora da faixa')
        by_key[int(n)].append((float(t),float(depth),int(vel)))
    dt=1./cfg.simulation_hz
    count=math.ceil(length*cfg.simulation_hz)
    reset=(cfg.double_reset_fraction if mode=='double' else cfg.single_reset_fraction)
    rearm=(cfg.backcheck_double_ms if mode=='double' else cfg.backcheck_single_ms)*.001
    scheduled=[];impacts=[];blocked=[];rearmlist=[];traj={}
    for midi,commands in sorted(by_key.items()):
        # Release antes de press ao mesmo tempo, para duracoes zero/legato.
        commands.sort(key=lambda e:(e[0],e[1]))
        position=0.;target=0.;current_vel=90;state='ready';flight_end=None
        last_impact=-1e9;crossings=0;holds=[]
        positions=[];strikes_for_note=[];cmd_index=0
        last_pressed_time=0.
        for i in range(count):
            t=i*dt
            while cmd_index<len(commands) and commands[cmd_index][0]<=t+1e-10:
                ct,dep,vel=commands[cmd_index]
                target=dep
                if dep>position+1e-9 and vel>0:current_vel=vel
                if dep>=cfg.escapement_key_fraction:last_pressed_time=ct
                cmd_index+=1
            prev=position
            down_rate=cfg.key_speed_ratio*_hammer_speed(current_vel)/(.001*cfg.key_dip_mm)
            up_rate=cfg.key_release_speed_m_s/(.001*cfg.key_dip_mm)
            movement=down_rate*dt if target>=position else -up_rate*dt
            position=(min(target,position+movement) if movement>0
                      else max(target,position+movement))
            if include_trajectories and i%10==0:
                positions.append((round(t,5),round(position,5),state))
            if state=='flying' and flight_end is not None and t+1e-12>=flight_end['impact_s']:
                # O martelo ja escapou e pode colidir mesmo que a tecla seja solta.
                strike=dict(flight_end)
                strike['midi']=midi
                strike['position_at_impact']=round(position,5)
                strikes_for_note.append(strike)
                impacts.append(strike)
                last_impact=t
                state='checked';flight_end=None
            if state=='checked' and position<=reset:
                # Backcheck nao equivale a jack rearmado; requer tempo minimo.
                state='rearming'
                rearmlist.append({'midi':midi,'at_s':round(t,5),'key_position':round(position,4)})
            if state=='rearming' and position<=reset and t>=last_impact+rearm:
                state='ready'
            if state=='rearming' and position>reset:
                # Rearme incompleto: a tecla voltou a subir cedo demais.
                state='checked'
            if prev<cfg.escapement_key_fraction<=position:
                crossings+=1
                if state=='ready':
                    speed=_hammer_speed(current_vel)
                    flight=cfg.hammer_flight_mm*.001/max(speed,1e-9)
                    speed_impact=speed*math.exp(-cfg.hammer_flight_drag_per_s*flight)
                    flight_end={'command_at_s':last_pressed_time,
                      'escapement_at_s':round(t,6),
                      'impact_s':round(t+flight,6),
                      'hammer_speed_m_s':speed_impact,
                      'velocity_midi':_velocity_from_speed(speed_impact),
                      'key_speed_m_s':cfg.key_speed_ratio*speed,
                      'mode':mode}
                    state='flying'
                else:
                    blocked.append({'midi':midi,'at_s':round(t,6),'reason':'jack_not_reset',
                                    'state':state})
            holds.append(position)
        # Cada impacto fica sustentado ate a tecla cair abaixo do limiar de
        # retorno do abafador, ou ate o fim da sequencia; nao é meia-pedal.
        for strike in strikes_for_note:
            impact_t=strike['impact_s']
            idx=min(count-1,max(0,round(impact_t*cfg.simulation_hz)))
            e=length
            # Saltos por amostras discretas apenas na fase de agendamento.
            for k in range(idx+1,count):
                if holds[k]<=cfg.damper_release_fraction:
                    e=k*dt
                    break
            dur=max(.012,e-impact_t)
            scheduled.append((impact_t,midi,dur,strike['velocity_midi']))
            strike['key_off_s']=round(e,6)
        if include_trajectories:traj[midi]=positions
    scheduled.sort(key=lambda e:(e[0],e[1]))
    impacts.sort(key=lambda e:(e['impact_s'],e['midi']))
    diagnostics={'action_events':impacts,'keyframe_count':len(cmds),'blocked_events':blocked,
        'blocked_count':len(blocked),'strike_count':len(impacts),'rearm_events':rearmlist,
        'unique_key_count':len(by_key),'mode':mode,
        'key_trajectories':traj if include_trajectories else None}
    return scheduled,diagnostics
