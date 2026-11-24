"""Mecânica de tecla/martelo/escapamento experimental do Stage Synth C3X V9.

NÃO contém medidas verificadas do Yamaha C3X. O agendamento simplifica o
sistema de alavancas e nunca substitui o contato não linear martelo–corda.
Nenhuma gravação é usada para produzir eventos ou áudio.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class GrandActionConfig:
    key_dip_mm: float = 10.0
    let_off_gap_mm: float = 1.7
    key_action_latency_ms: float = 5.5
    flight_drag_per_s: float = 3.0
    double_escapement_reset_ms: float = 12.0
    single_escapement_reset_ms: float = 35.0
    key_motion_factor: float = 1.0
    felt_rate_exponent: float = 0.055

    def validate(self):
        vals = vars(self).values()
        if not all(math.isfinite(float(v)) for v in vals):
            raise ValueError('Parâmetros de ação não finitos')
        if not (5 <= self.key_dip_mm <= 13 and .3 <= self.let_off_gap_mm <= 5
                and 0 <= self.key_action_latency_ms <= 50 and 0 <= self.flight_drag_per_s <= 30
                and 3 <= self.double_escapement_reset_ms <= 80
                and self.double_escapement_reset_ms <= self.single_escapement_reset_ms <= 120
                and .2 <= self.key_motion_factor <= 3
                and 0 <= self.felt_rate_exponent <= .18):
            raise ValueError('Ação fora das faixas experimentais')
        return self


def _hammer_speed(velocity):
    return .45+(velocity/127.)**1.45*(2.6-.45)


def _velocity_from_speed(speed):
    frac=max(0.,min(1.,(speed-.45)/(2.6-.45)))
    return max(1,min(127,round(127*frac**(1/1.45))))


def schedule_grand_action(events,length,config=None,mode='double',bypass=False):
    """Converte (pressionamento,MIDI,duração,vel.) em impactos calculados.

    O modo double re-arma após curta liberação da tecla, comparado a single.
    Eventos rearmados tarde têm o golpe atrasado, não são sobrepostos.
    A V9 usa um MESMO conjunto de cordas para impactos repetidos.
    """
    cfg=(config or GrandActionConfig()).validate()
    if mode not in ('double','single'):
        raise ValueError('Modo de escapamento desconhecido')
    if not (math.isfinite(length) and 0<length<=60):
        raise ValueError('Duração inválida')
    evs=[]
    for ev in events:
        if len(ev)!=4 or not all(math.isfinite(float(x)) for x in ev):
            raise ValueError('Evento de teclado inválido')
        t,n,hold,vel=ev
        if not (0<=t<=length and 0<=hold and isinstance(n,(int,float))
                and int(n)==n and 21<=n<=108 and isinstance(vel,(int,float))
                and int(vel)==vel and 1<=vel<=127):
            raise ValueError('Evento de teclado fora de faixa')
        if float(t)<length:evs.append((float(t),int(n),float(hold),int(vel)))
    evs.sort(key=lambda e:(e[0],e[1]))
    prev_release={}
    result=[]
    measurements=[]
    for t,n,hold,vel in evs:
        if bypass:
            onset=t;effvel=vel;latency=0.;rearm_delay=0.
        else:
            speed=_hammer_speed(vel)
            key_time_s=cfg.key_motion_factor*(cfg.key_dip_mm*.001)/speed
            flight_time_s=(cfg.let_off_gap_mm*.001)/speed
            latency=.001*cfg.key_action_latency_ms+key_time_s+flight_time_s
            # O martelo segue em voo após o escapamento (sem ação da tecla).
            exit_speed=speed*math.exp(-cfg.flight_drag_per_s*flight_time_s)
            effvel=_velocity_from_speed(exit_speed)
            reset=(cfg.double_escapement_reset_ms if mode=='double'
                    else cfg.single_escapement_reset_ms)*.001
            ready=prev_release.get(n,-1e9)+reset
            nominal=t+latency
            onset=max(nominal,ready)
            rearm_delay=max(0.,onset-nominal)
        # O abafador da nota recém-atacada volta quando a tecla é liberada.
        key_off=t+hold
        effective_hold=max(.012,key_off-onset)
        if onset<length:
            result.append((onset,n,effective_hold,effvel))
            measurements.append({'midi':n,'pressed_at_s':t,'strike_at_s':onset,
                'latency_ms':round(1000*latency,3),'requested_velocity':vel,
                'effective_velocity':effvel,'rearm_wait_ms':round(1000*rearm_delay,3),
                'key_off_s':key_off})
        prev_release[n]=max(prev_release.get(n,-1e9),key_off)
    return result,measurements
