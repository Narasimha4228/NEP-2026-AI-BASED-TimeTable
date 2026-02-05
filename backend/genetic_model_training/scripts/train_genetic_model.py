"""
Genetic Model Training Script
Trains the genetic algorithm model for timetable generation
"""

import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from typing import List, Dict, Tuple, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class GeneticModelTrainer:
    """Trainer for genetic algorithm timetable model"""
    
    def __init__(self, 
                 population_size: int = 50,
                 generations: int = 100,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.8):
        """
        Initialize the trainer
        
        Args:
            population_size: Size of population per generation
            generations: Number of generations to train
            mutation_rate: Probability of mutation
            crossover_rate: Probability of crossover
        """
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.training_history = []
        self.best_solutions = []
        
    def load_training_data(self, data_path: str) -> Dict[str, Any]:
        """Load training data from JSON file"""
        with open(data_path, 'r') as f:
            return json.load(f)
    
    def save_training_data(self, data_path: str, data: Dict[str, Any]):
        """Save training data to JSON file"""
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        with open(data_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_chromosome(self, constraints: Dict) -> List[int]:
        """Create a random chromosome (timetable assignment)"""
        num_entries = constraints.get('num_entries', 50)
        num_slots = constraints.get('num_slots', 25)
        return [random.randint(0, num_slots - 1) for _ in range(num_entries)]
    
    def evaluate_fitness(self, chromosome: List[int], constraints: Dict) -> float:
        """
        Evaluate fitness of a chromosome
        Lower score is better (fewer conflicts)
        """
        score = 0
        
        # Penalty for various constraint violations
        num_conflicts = constraints.get('conflicts', 0)
        score += num_conflicts * 10
        
        # Penalty for room utilization imbalance
        room_usage = {}
        for slot in chromosome:
            room_usage[slot] = room_usage.get(slot, 0) + 1
        
        avg_usage = len(chromosome) / len(room_usage) if room_usage else 0
        for usage in room_usage.values():
            score += abs(usage - avg_usage)
        
        return score
    
    def crossover(self, parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
        """Single-point crossover"""
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()
        
        crossover_point = random.randint(1, len(parent1) - 1)
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]
        
        return child1, child2
    
    def mutate(self, chromosome: List[int], constraints: Dict) -> List[int]:
        """Mutate a chromosome"""
        if random.random() > self.mutation_rate:
            return chromosome.copy()
        
        num_slots = constraints.get('num_slots', 25)
        mutation_point = random.randint(0, len(chromosome) - 1)
        mutated = chromosome.copy()
        mutated[mutation_point] = random.randint(0, num_slots - 1)
        
        return mutated
    
    def select_parents(self, population: List[Tuple[List[int], float]], 
                      tournament_size: int = 3) -> List[int]:
        """Tournament selection"""
        tournament = random.sample(range(len(population)), tournament_size)
        best_idx = min(tournament, key=lambda i: population[i][1])
        return population[best_idx][0]
    
    def train(self, constraints: Dict) -> Dict[str, Any]:
        """
        Train the genetic model
        
        Args:
            constraints: Training constraints and parameters
            
        Returns:
            Training results and statistics
        """
        print(f"Starting training with {self.generations} generations...")
        print(f"Population size: {self.population_size}")
        
        # Initialize population
        population = [
            (self.create_chromosome(constraints), float('inf'))
            for _ in range(self.population_size)
        ]
        
        for generation in range(self.generations):
            # Evaluate fitness
            for i, (chromosome, _) in enumerate(population):
                fitness = self.evaluate_fitness(chromosome, constraints)
                population[i] = (chromosome, fitness)
            
            # Sort by fitness (lower is better)
            population.sort(key=lambda x: x[1])
            
            # Track best solution
            best_solution = {
                'generation': generation,
                'fitness': population[0][1],
                'chromosome': population[0][0][:10]  # First 10 genes for brevity
            }
            self.best_solutions.append(best_solution)
            
            if generation % 10 == 0:
                print(f"Generation {generation}: Best fitness = {population[0][1]:.2f}")
            
            # Create new population (elitism)
            elite_size = max(1, self.population_size // 10)
            new_population = population[:elite_size]
            
            # Generate offspring
            while len(new_population) < self.population_size:
                parent1 = self.select_parents(population)
                parent2 = self.select_parents(population)
                child1, child2 = self.crossover(parent1, parent2)
                child1 = self.mutate(child1, constraints)
                child2 = self.mutate(child2, constraints)
                new_population.append((child1, float('inf')))
                if len(new_population) < self.population_size:
                    new_population.append((child2, float('inf')))
            
            population = new_population[:self.population_size]
        
        # Final evaluation
        for i, (chromosome, _) in enumerate(population):
            fitness = self.evaluate_fitness(chromosome, constraints)
            population[i] = (chromosome, fitness)
        
        population.sort(key=lambda x: x[1])
        
        training_results = {
            'timestamp': datetime.now().isoformat(),
            'generations': self.generations,
            'population_size': self.population_size,
            'mutation_rate': self.mutation_rate,
            'crossover_rate': self.crossover_rate,
            'best_fitness': population[0][1],
            'best_chromosome': population[0][0],
            'convergence_history': self.best_solutions,
            'constraints': constraints
        }
        
        return training_results
    
    def save_model(self, model_data: Dict[str, Any], output_path: str):
        """Save trained model"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(model_data, f, indent=2)
        print(f"Model saved to {output_path}")
    
    def generate_report(self, results: Dict[str, Any], report_path: str):
        """Generate training report"""
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        report = f"""
# Genetic Model Training Report
Generated: {results['timestamp']}

## Training Configuration
- Generations: {results['generations']}
- Population Size: {results['population_size']}
- Mutation Rate: {results['mutation_rate']}
- Crossover Rate: {results['crossover_rate']}

## Results
- Best Fitness: {results['best_fitness']:.4f}
- Convergence History Length: {len(results['convergence_history'])}

## Convergence Progress
Generation | Fitness
-----------|----------
"""
        for entry in results['convergence_history'][::max(1, len(results['convergence_history'])//20)]:
            report += f"{entry['generation']:>10} | {entry['fitness']:>8.4f}\n"
        
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"Report saved to {report_path}")


def main():
    """Main training function"""
    print("=== Genetic Model Training ===\n")
    
    # Default constraints
    constraints = {
        'num_entries': 100,
        'num_slots': 50,
        'num_rooms': 10,
        'conflicts': 5,
        'max_hours_per_day': 8,
        'min_break_between_classes': 15
    }
    
    # Initialize trainer
    trainer = GeneticModelTrainer(
        population_size=50,
        generations=100,
        mutation_rate=0.1,
        crossover_rate=0.8
    )
    
    # Train model
    results = trainer.train(constraints)
    
    # Save model and report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_output = f"../models/genetic_model_{timestamp}.json"
    report_output = f"../results/training_report_{timestamp}.md"
    
    trainer.save_model(results, model_output)
    trainer.generate_report(results, report_output)
    
    print("\n=== Training Complete ===")
    print(f"Best fitness achieved: {results['best_fitness']:.4f}")


if __name__ == "__main__":
    main()
