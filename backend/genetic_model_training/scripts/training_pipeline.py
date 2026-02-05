"""
Complete Training Pipeline for Genetic Model
Orchestrates data preparation, model training, and evaluation
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from prepare_data import TrainingDataPreparator
from train_genetic_model import GeneticModelTrainer


class TrainingPipeline:
    """Main training pipeline orchestrator"""
    
    def __init__(self, config_path: str = None):
        """Initialize the pipeline"""
        self.base_dir = Path(__file__).parent.parent
        self.config = self._load_config(config_path)
        self.data_dir = self.base_dir / "data"
        self.model_dir = self.base_dir / "models"
        self.results_dir = self.base_dir / "results"
        
        # Create directories
        self.data_dir.mkdir(exist_ok=True)
        self.model_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if config_path is None:
            config_path = self.base_dir / "config.json"
        
        if not os.path.exists(config_path):
            # Return default config
            return {
                'hyperparameters': {
                    'population_size': 50,
                    'generations': 100,
                    'mutation_rate': 0.1,
                    'crossover_rate': 0.8
                },
                'constraints': {
                    'num_entries': 150,
                    'num_slots': 60,
                    'num_rooms': 15
                }
            }
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def prepare_data(self, force_regenerate: bool = False) -> str:
        """Prepare training data"""
        print("\n" + "=" * 60)
        print("STEP 1: Preparing Training Data")
        print("=" * 60)
        
        data_file = self.data_dir / "training_data.json"
        
        if data_file.exists() and not force_regenerate:
            print(f"Training data already exists: {data_file}")
            return str(data_file)
        
        preparator = TrainingDataPreparator(output_dir=str(self.data_dir))
        training_data = preparator.prepare_training_data()
        data_path = preparator.save_training_data(training_data)
        
        return data_path
    
    def train_model(self, training_data_path: str) -> Dict[str, Any]:
        """Train the genetic model"""
        print("\n" + "=" * 60)
        print("STEP 2: Training Genetic Model")
        print("=" * 60)
        
        # Load training data
        with open(training_data_path, 'r') as f:
            training_data = json.load(f)
        
        # Get hyperparameters from config
        hp = self.config.get('hyperparameters', {})
        
        # Initialize trainer
        trainer = GeneticModelTrainer(
            population_size=hp.get('population_size', 50),
            generations=hp.get('generations', 100),
            mutation_rate=hp.get('mutation_rate', 0.1),
            crossover_rate=hp.get('crossover_rate', 0.8)
        )
        
        # Get constraints
        constraints = training_data.get('constraints', 
                                       self.config.get('constraints', {}))
        
        # Train
        results = trainer.train(constraints)
        
        return results
    
    def save_results(self, training_results: Dict[str, Any]):
        """Save training results and model"""
        print("\n" + "=" * 60)
        print("STEP 3: Saving Results")
        print("=" * 60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save model
        model_file = self.model_dir / f"genetic_model_{timestamp}.json"
        with open(model_file, 'w') as f:
            json.dump(training_results, f, indent=2)
        print(f"Model saved: {model_file}")
        
        # Generate report
        report_file = self.results_dir / f"training_report_{timestamp}.md"
        self._generate_report(training_results, report_file)
        
        # Save summary
        summary_file = self.results_dir / f"training_summary_{timestamp}.json"
        summary = {
            'timestamp': training_results['timestamp'],
            'generations': training_results['generations'],
            'population_size': training_results['population_size'],
            'best_fitness': training_results['best_fitness'],
            'model_file': str(model_file),
            'report_file': str(report_file)
        }
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Summary saved: {summary_file}")
    
    def _generate_report(self, results: Dict[str, Any], report_path: Path):
        """Generate training report"""
        report = f"""# Genetic Model Training Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Training Configuration
- **Generations**: {results['generations']}
- **Population Size**: {results['population_size']}
- **Mutation Rate**: {results['mutation_rate']}
- **Crossover Rate**: {results['crossover_rate']}

## Training Results
- **Best Fitness Score**: {results['best_fitness']:.4f}
- **Convergence Steps**: {len(results['convergence_history'])}

## Convergence History
| Generation | Fitness Score |
|------------|---------------|
"""
        
        # Sample convergence history
        history = results['convergence_history']
        sample_indices = list(range(0, len(history), max(1, len(history)//20)))
        
        for idx in sample_indices:
            if idx < len(history):
                entry = history[idx]
                report += f"| {entry['generation']:>10} | {entry['fitness']:>13.4f} |\n"
        
        report += f"""
## Model Information
- **Best Chromosome (first 10 genes)**: {results['best_chromosome'][:10]}
- **Chromosome Length**: {len(results['best_chromosome'])}

## Constraints Used
"""
        for key, value in results['constraints'].items():
            report += f"- **{key}**: {value}\n"
        
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"Report saved: {report_path}")
    
    def run(self, force_regenerate_data: bool = False):
        """Run the complete pipeline"""
        print("\n" + "=" * 60)
        print("GENETIC MODEL TRAINING PIPELINE")
        print("=" * 60)
        
        try:
            # Step 1: Prepare data
            training_data_path = self.prepare_data(force_regenerate_data)
            
            # Step 2: Train model
            training_results = self.train_model(training_data_path)
            
            # Step 3: Save results
            self.save_results(training_results)
            
            print("\n" + "=" * 60)
            print("✓ PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print(f"Best fitness achieved: {training_results['best_fitness']:.4f}")
            print(f"Models saved to: {self.model_dir}")
            print(f"Results saved to: {self.results_dir}")
            
        except Exception as e:
            print(f"\n✗ ERROR: {str(e)}")
            raise


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Genetic Model Training Pipeline')
    parser.add_argument('--force-data', action='store_true', 
                       help='Force regeneration of training data')
    parser.add_argument('--config', type=str, 
                       help='Path to config file')
    
    args = parser.parse_args()
    
    pipeline = TrainingPipeline(config_path=args.config)
    pipeline.run(force_regenerate_data=args.force_data)


if __name__ == "__main__":
    main()
