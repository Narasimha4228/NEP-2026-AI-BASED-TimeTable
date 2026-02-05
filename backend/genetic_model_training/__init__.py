"""
Genetic Model Training Package
For timetable scheduling optimization using genetic algorithms
"""

__version__ = "1.0.0"
__author__ = "NEP Timetable AI"

from scripts.prepare_data import TrainingDataPreparator
from scripts.train_genetic_model import GeneticModelTrainer
from scripts.training_pipeline import TrainingPipeline

__all__ = [
    'TrainingDataPreparator',
    'GeneticModelTrainer',
    'TrainingPipeline'
]
