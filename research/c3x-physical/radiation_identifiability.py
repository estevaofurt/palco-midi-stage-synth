"""F1.5: controlled Rayleigh-point quadrature for illustrative soundboard radiation.

This module is NOT a Yamaha C3X/C5 acoustic model, and it is NOT integrated into
any sound engine. It only checks the informational content of possible recordings.

Using the baffled-plane, monopole approximation for surface patches:
  p(x, f) = j*rho*omega/(2*pi) * sum_i A_i v_i exp(-j*k*r_i)/r_i.
Here pressure p is [Pa], surface normal velocities v_i [m/s], areas [m²],
receiver distances r_i [m], rho [kg/m³], and k=omega/c. The approximate
radiated pressure neglects panel/air back-reaction, finite baffle, room,
and distributed velocities within a patch. The signs of v_i encode mode shapes.
"""
from __future__ import annotations
import cmath
import math
from dataclasses import dataclass

RHO = 1.20  # kg / m³, illustrative reference condition; not measured
C = 343.0  # m/s, illustrative reference condition; not measured

@dataclass(frozen=True)
class Patch:
    location_m: tuple[float, float, float]
    area_m2: float
    normal_velocity_m_s: complex


def pressure_rayleigh_patches(patches, receiver_m, frequency_hz, density_kg_m3=RHO, speed_m_s=C):
    """Return frequency-domain pressure phasor [Pa]; single-side baffled approximation."""
    if not 0 < frequency_hz < 20000 or not math.isfinite(frequency_hz):
        raise ValueError('finite positive frequency <20 kHz required')
    if not all(math.isfinite(v) for v in (density_kg_m3, speed_m_s)) or density_kg_m3<=0 or speed_m_s<=0:
        raise ValueError('invalid fluid parameters')
    if len(receiver_m) != 3 or not all(math.isfinite(v) for v in receiver_m):
        raise ValueError('receiver coordinates required in meters')
    if not patches:
        raise ValueError('at least one patch required')
    omega=2*math.pi*frequency_hz
    k=omega/speed_m_s
    total=complex(0,0)
    for patch in patches:
        if patch.area_m2<=0 or not math.isfinite(patch.area_m2) or len(patch.location_m)!=3:
            raise ValueError('patch area and location required')
        if not all(math.isfinite(v) for v in patch.location_m) or not all(math.isfinite(v) for v in (patch.normal_velocity_m_s.real,patch.normal_velocity_m_s.imag)):
            raise ValueError('patch position and velocity must be finite')
        d=math.dist(receiver_m,patch.location_m)
        if d<=1e-6:
            raise ValueError('receiver cannot coincide with source')
        total+= patch.area_m2*patch.normal_velocity_m_s*cmath.exp(-1j*k*d)/d
    return (1j*density_kg_m3*omega/(2*math.pi))*total


def pressure_only_factorization(source_phasor, transfer_phasor, arbitrary_gain):
    """Two indistinguishable (source, transfer) pairs from *one* observed P=SH.

    Abstract phasor math; input/output sensors are deliberately unspecified.
    This proves a single output recording alone cannot identify S and H.
    """
    if abs(arbitrary_gain)<1e-12:
        raise ValueError('nonzero factor required')
    observed=source_phasor*transfer_phasor
    changed_source=source_phasor*arbitrary_gain
    changed_transfer=transfer_phasor/arbitrary_gain
    if not math.isclose(abs(changed_source*changed_transfer-observed),0.,abs_tol=1e-11):
        raise AssertionError('factorization identity failed')
    return {'pressure_original':observed,'pressure_alternate':changed_source*changed_transfer,
            'source_original':source_phasor,'transfer_original':transfer_phasor,
            'source_alternate':changed_source,'transfer_alternate':changed_transfer}


def synthetic_radiation_example():
    """Two fictitious 0.04 m² patches at +/-0.24m; phases are *assumed*, NOT fitted."""
    f0=261.6255653005986
    B=0.0005284491799769235  # from V10 as *estimated*, not C3X physics
    frequency=lambda n:f0*n*math.sqrt((1+B*n*n)/(1+B))
    mic_positions={'center':(0.,0.,1.),'offset':(.50,0.,1.),'far_offset':(1.,0.,1.)}
    cases={}
    for partial in (4,5):
        # This is a demonstrative, chosen modal pattern. It says NOTHING about a real C3X.
        signs=(1.,1.) if partial==4 else (1.,-1.)
        patches=[Patch((-0.24,0.,0.),.04,signs[0]*.001),Patch((.24,0.,0.),.04,signs[1]*.001)]
        cases[str(partial)]={name:pressure_rayleigh_patches(patches,mic,frequency(partial)) for name,mic in mic_positions.items()}
    return cases


def normalized_synthetic_summary():
    cases=synthetic_radiation_example()
    result={}
    for name in ('center','offset','far_offset'):
        h4=abs(cases['4'][name]);h5=abs(cases['5'][name])
        result[name]={'partial4_pressure_magnitude_Pa':h4,
                      'partial5_pressure_magnitude_Pa':h5,
                      'h5_relative_to_h4_db':20*math.log10(max(h5,1e-18)/max(h4,1e-18))}
    return result
