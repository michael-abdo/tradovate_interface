"""
DEAD Simple Volume Spike Analysis Module
Detect and follow institutional money flow
"""

from .solution import DeadSimpleVolumeSpike, InstitutionalSignal, create_dead_simple_analyzer

__all__ = ['DeadSimpleVolumeSpike', 'InstitutionalSignal', 'create_dead_simple_analyzer']