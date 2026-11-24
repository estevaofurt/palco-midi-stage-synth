from .parameters import note_params, YAMAHA_C3X, save_scale_csv
from .engine import render_note, render_sequence, SR
__all__ = ['note_params','YAMAHA_C3X','save_scale_csv','render_note','render_sequence','SR','tune_note','tuning_cents','anchor_stretch_cents','FeedbackConfig',
           'render_note_feedback','render_sequence_feedback','string_soundboard_feedback']

from .tuning import tune_note,tuning_cents,anchor_stretch_cents
from .feedback import FeedbackConfig,render_note_feedback,render_sequence_feedback,string_soundboard_feedback
from .pedals import DamperConfig, render_sequence_pedals, cc64_to_pedal_events
__all__ += ['DamperConfig','render_sequence_pedals','cc64_to_pedal_events']

from .optimized import render_sequence_v8  # V8 estrita: bit a bit equivalente a V7
from .optimized_coeff import render_sequence_v8_coeff  # V8 rapida: coeficientes precomputados
__all__ += ['render_sequence_v8', 'render_sequence_v8_coeff']

from .action import GrandActionConfig, schedule_grand_action
from .action_engine import render_sequence_v9_action
__all__ += ['GrandActionConfig','schedule_grand_action','render_sequence_v9_action']
