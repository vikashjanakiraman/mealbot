"""Seed FoodDatabase with foods from CSV"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import csv
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.food_database import FoodDatabase


def seed_foods():
    """Load foods from CSV and populate database"""
    db: Session = SessionLocal()
    
    try:
        # Check if already seeded
        existing_count = db.query(FoodDatabase).count()
        if existing_count > 0:
            print(f"⚠️  Database already has {existing_count} foods!")
            response = input("Reseed anyway? (yes/no): ")
            if response.lower() != 'yes':
                print("Skipping seed.")
                return
            # Clear existing
            db.query(FoodDatabase).delete()
            db.commit()
            print(f"✓ Cleared {existing_count} existing foods")
        
        # Read CSV and seed
        foods_added = 0
        with open('scripts/data/foods.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                food = FoodDatabase(
                    food_name=row['food_name'],
                    default_calories=int(row['default_calories']),
                    protein_g=float(row['protein_g']),
                    carbs_g=float(row['carbs_g']),
                    fats_g=float(row['fats_g']),
                    category=row['category'],
                    cuisine=row.get('cuisine'),
                    diet_type=row.get('diet_type'),
                    aliases=row.get('aliases')
                )
                db.add(food)
                foods_added += 1
                
                # Print progress every 50 foods
                if foods_added % 50 == 0:
                    print(f"  Added {foods_added} foods...")
        
        # Commit all
        db.commit()
        print(f"\n✓ Seeded {foods_added} foods successfully!")
        
        # Verify
        count = db.query(FoodDatabase).count()
        print(f"✓ Total foods in database: {count}")
        
        # Show sample
        samples = db.query(FoodDatabase).limit(5).all()
        print(f"\nSample foods:")
        for food in samples:
            print(f"  - {food.food_name}: {food.default_calories} cal, {food.protein_g}g protein")
        
    except FileNotFoundError:
        print("✗ foods.csv not found!")
        print(f"  Expected at: scripts/data/foods.csv")
        return
    except Exception as e:
        print(f"✗ Error seeding database: {e}")
        db.rollback()
        return
    finally:
        db.close()


if __name__ == "__main__":
    print("="*60)
    print("SEEDING FOODDATABASE")
    print("="*60)
    seed_foods()
    print("\n✓ SEEDING COMPLETE")
