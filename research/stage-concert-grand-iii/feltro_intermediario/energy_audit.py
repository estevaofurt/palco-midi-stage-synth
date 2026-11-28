"""Read-only audit for the single-hammer physical integration.
Exterior work is signed cumulative work, not assumed radiated energy.
No state, force, coefficient or time step is modified here.
"""
import math

def audit_partition(initial,mass,speed,impulse,stores,target_losses,felt_loss,capture_loss,combined_loss,combined_storage):
    assert set(stores)=={'mechanical','cavity','hammer_kinetic','felt'}
    assert set(target_losses)=={'mechanical','cavity','exterior_work'}
    values=[initial,mass,speed,impulse,felt_loss,capture_loss,combined_loss,combined_storage,*stores.values(),*target_losses.values()]
    assert all(math.isfinite(x) for x in values)
    assert initial>0 and mass>0 and speed>0 and impulse>=0
    assert all(x>=-1e-12*initial for x in stores.values())
    assert felt_loss>=0 and capture_loss>=0
    assert target_losses['mechanical']>=-1e-12*initial and target_losses['cavity']>=-1e-12*initial
    # Signed exterior work remains separate; do not clip a negative value.
    losses={**target_losses,'felt':felt_loss,'capture':capture_loss}
    v=speed-impulse/mass
    assert v<0, 'Impulse does not establish a rebound at capture'
    predicted=.5*mass*v*v
    errors=dict(initial_kinetic=abs(initial-.5*mass*speed*speed)/initial,
                storage_partition=abs(math.fsum(stores.values())-combined_storage)/initial,
                target_loss_partition=abs(math.fsum(target_losses.values())-combined_loss)/initial,
                capture_from_impulse=abs(predicted-capture_loss)/initial,
                full_balance=abs(math.fsum([*stores.values(),*losses.values()])-initial)/initial)
    assert max(errors.values())<1e-8, errors
    assert abs(stores['hammer_kinetic'])<1e-12*initial, 'Hammer not captured'
    return dict(initial_J=initial, mass_kg=mass, launch_speed_mps=speed, impulse_Ns=impulse,
                rebound_velocity_from_impulse_mps=v, inferred_capture_J=predicted,
                stored_J=dict(stores),loss_J=losses,relative_errors=errors)
