# Genetic Model Training

This folder contains the complete training infrastructure and scripts for the genetic algorithm model used in timetable generation.

## Overview

The genetic model training system provides:
- **Automated data preparation** - Generate training datasets automatically
- **Genetic algorithm implementation** - State-of-the-art GA training
- **Model evaluation** - Comprehensive fitness evaluation and convergence tracking
- **Result analysis** - Detailed reports and statistics

## Folder Structure

```
genetic_model_training/
├── scripts/              # Training scripts and utilities
│   ├── prepare_data.py             # Data preparation and generation
│   ├── train_genetic_model.py       # Core genetic algorithm trainer
│   └── training_pipeline.py         # Complete orchestration pipeline
├── data/                # Training datasets
│   ├── training_data.json           # Main training dataset
│   └── validation_data.json         # Validation dataset
├── models/              # Trained model files
│   └── genetic_model_[timestamp].json
├── results/             # Training results and reports
│   ├── training_report_[timestamp].md
│   └── training_summary_[timestamp].json
├── config.json         # Configuration file
└── README.md           # This file
```

## Quick Start

### 1. Prepare Training Data
```bash
python scripts/prepare_data.py
```
This generates training data with sample courses, instructors, rooms, and student groups.

### 2. Run Complete Pipeline
```bash
python scripts/training_pipeline.py
```
This runs the complete training pipeline:
- Prepares data (if not exists)
- Trains the genetic model
- Saves model and generates report

### 3. Run with Options
```bash
# Force regenerate training data
python scripts/training_pipeline.py --force-data

# Use custom config
python scripts/training_pipeline.py --config custom_config.json
```

## Configuration

Edit `config.json` to customize training parameters:

```json
{
  "hyperparameters": {
    "population_size": 50,        # GA population size
    "generations": 100,           # Number of generations
    "mutation_rate": 0.1,         # Mutation probability
    "crossover_rate": 0.8         # Crossover probability
  },
  "constraints": {
    "num_entries": 150,           # Classes to schedule
    "num_slots": 60,              # Available time slots
    "num_rooms": 15,              # Number of rooms
    "num_instructors": 25,        # Number of instructors
    "num_courses": 30             # Number of courses
  }
}
```

## Training Process

### 1. Data Preparation (`prepare_data.py`)
- Creates sample courses, instructors, rooms, and student groups
- Generates constraint definitions
- Produces training and validation datasets

### 2. Genetic Algorithm Training (`train_genetic_model.py`)
- Initializes random population
- Evaluates fitness for each generation
- Performs selection, crossover, and mutation
- Tracks convergence history
- Saves best solutions

### 3. Pipeline Orchestration (`training_pipeline.py`)
- Coordinates all training steps
- Generates comprehensive reports
- Saves model checkpoints
- Creates summary statistics

## Output Files

### Models (`models/` folder)
- Complete trained model with convergence history
- Best chromosome (timetable solution)
- Training configuration

### Results (`results/` folder)
- **training_report_[timestamp].md** - Detailed training report with convergence graphs
- **training_summary_[timestamp].json** - Summary statistics

### Data (`data/` folder)
- **training_data.json** - Full training dataset
- **validation_data.json** - Validation dataset for model evaluation

## Key Scripts

### `prepare_data.py`
Generates training and validation datasets with:
- 30+ courses across 5 departments
- 25 instructors
- 15 classrooms with different capabilities
- 100+ student groups

### `train_genetic_model.py`
Core GA trainer with:
- Tournament selection
- Single-point crossover
- Gaussian mutation
- Elitism strategy
- Fitness-based evaluation

### `training_pipeline.py`
Main orchestrator that:
- Manages the complete workflow
- Handles configuration
- Generates reports
- Saves models and results

## Requirements

Install required packages:
```bash
pip install -r requirements.txt
```

Dependencies:
- numpy - Numerical computing
- scipy - Scientific computing
- matplotlib - Visualization
- pandas - Data manipulation
- scikit-learn - Machine learning utilities

## Understanding Results

### Best Fitness Score
Lower values indicate better solutions. The algorithm tries to minimize:
- Room scheduling conflicts
- Instructor availability violations
- Student group overlaps
- Workload imbalance

### Convergence History
Shows how the best fitness improves over generations. Flat sections indicate convergence.

### Model Interpretation
The trained model contains:
- **chromosome**: Array of room/time slot assignments
- **fitness**: Quality metric of the solution
- **constraints**: Scheduling rules used

## Advanced Usage

### Custom Data Preparation
Modify `TrainingDataPreparator` in `prepare_data.py` to:
- Add domain-specific constraints
- Customize course/instructor data
- Implement different room configurations

### Parameter Tuning
Adjust hyperparameters in `config.json`:
- Higher `population_size` = better quality but slower
- Higher `generations` = more optimization time
- Higher `mutation_rate` = more exploration
- Higher `crossover_rate` = more recombination

### Extending the Trainer
Inherit from `GeneticModelTrainer` to:
- Implement custom crossover strategies
- Add constraint validation
- Integrate domain knowledge
- Implement multi-objective optimization

## Troubleshooting

**Issue**: Module import errors
- Ensure you're running from the correct directory
- Check that parent dependencies are installed

**Issue**: Slow training
- Reduce `population_size` or `generations`
- Optimize constraint evaluation function

**Issue**: Poor convergence
- Increase `generations`
- Adjust mutation/crossover rates
- Check constraint feasibility

## License

This genetic model training system is part of the NEP Timetable AI project.
