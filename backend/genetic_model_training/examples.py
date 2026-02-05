"""
Example Usage of Genetic Model Training
Demonstrates how to use the training system
"""

import json
from scripts.prepare_data import TrainingDataPreparator
from scripts.train_genetic_model import GeneticModelTrainer
from scripts.training_pipeline import TrainingPipeline


def example_1_prepare_data():
    """Example 1: Prepare training data"""
    print("=" * 60)
    print("EXAMPLE 1: Preparing Training Data")
    print("=" * 60)
    
    preparator = TrainingDataPreparator(output_dir="data")
    training_data = preparator.prepare_training_data()
    preparator.save_training_data(training_data)
    preparator.save_validation_data()


def example_2_train_model():
    """Example 2: Train genetic model with custom constraints"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Training Genetic Model")
    print("=" * 60)
    
    # Define constraints
    constraints = {
        'num_entries': 100,
        'num_slots': 50,
        'num_rooms': 10,
        'conflicts': 5,
        'max_hours_per_day': 8
    }
    
    # Initialize trainer
    trainer = GeneticModelTrainer(
        population_size=40,
        generations=50,
        mutation_rate=0.15,
        crossover_rate=0.85
    )
    
    # Train model
    results = trainer.train(constraints)
    
    # Display results
    print(f"\nBest fitness: {results['best_fitness']:.4f}")
    print(f"Generations: {results['generations']}")
    
    # Save model
    trainer.save_model(results, "models/example_model.json")
    trainer.generate_report(results, "results/example_report.md")


def example_3_run_pipeline():
    """Example 3: Run complete training pipeline"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Running Complete Pipeline")
    print("=" * 60)
    
    pipeline = TrainingPipeline()
    pipeline.run()


def example_4_custom_training():
    """Example 4: Custom training with evaluation"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Custom Training with Evaluation")
    print("=" * 60)
    
    # Load custom constraints
    constraints = {
        'num_entries': 200,
        'num_slots': 80,
        'num_rooms': 20,
        'conflicts': 10,
        'max_hours_per_day': 8,
        'min_break': 15
    }
    
    # Create trainer with custom parameters
    trainer = GeneticModelTrainer(
        population_size=100,
        generations=200,
        mutation_rate=0.12,
        crossover_rate=0.85
    )
    
    # Train
    results = trainer.train(constraints)
    
    # Display convergence analysis
    history = results['convergence_history']
    print(f"\nConvergence Analysis:")
    print(f"Initial fitness: {history[0]['fitness']:.4f}")
    print(f"Final fitness: {history[-1]['fitness']:.4f}")
    print(f"Improvement: {(history[0]['fitness'] - history[-1]['fitness']):.4f}")
    
    # Find generation with best fitness
    best_gen = min(history, key=lambda x: x['fitness'])
    print(f"Best fitness at generation {best_gen['generation']}: {best_gen['fitness']:.4f}")


if __name__ == "__main__":
    # Run examples
    # Uncomment the examples you want to run:
    
    # example_1_prepare_data()
    # example_2_train_model()
    # example_3_run_pipeline()
    example_4_custom_training()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
