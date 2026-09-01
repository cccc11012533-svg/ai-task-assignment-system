import asyncio
import heapq
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import random

@dataclass
class Order:
    """Represents a delivery order"""
    order_id: str
    customer_location: tuple
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
@dataclass
class Driver:
    """Represents a delivery driver"""
    driver_id: str
    current_location: tuple
    available: bool = True
    active_orders: int = 0
    max_concurrent: int = 3

class TaskAssignmentAI:
    """AI system for fast task assignment with concurrent order processing"""
    
    def __init__(self, max_concurrent_orders: int = 3):
        self.max_concurrent = max_concurrent_orders
        self.pending_orders: List[Order] = []
        self.drivers: Dict[str, Driver] = {}
        self.assignments: Dict[str, str] = {}  # order_id -> driver_id
        
    def add_driver(self, driver: Driver):
        """Register a driver in the system"""
        self.drivers[driver.driver_id] = driver
        
    def calculate_distance(self, loc1: tuple, loc2: tuple) -> float:
        """Quick distance calculation"""
        return ((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)**0.5
    
    async def assign_task(self, order: Order) -> Optional[str]:
        """Fast AI assignment - finds best driver instantly"""
        if not self.drivers:
            self.pending_orders.append(order)
            return None
            
        # Find available drivers with capacity
        available_drivers = [
            d for d in self.drivers.values() 
            if d.available and d.active_orders < self.max_concurrent
        ]
        
        if not available_drivers:
            self.pending_orders.append(order)
            return None
        
        # AI scoring: priority + distance + load
        best_driver = min(
            available_drivers,
            key=lambda d: (
                self.calculate_distance(d.current_location, order.customer_location),
                d.active_orders,
                -order.priority
            )
        )
        
        # Assign immediately
        best_driver.active_orders += 1
        self.assignments[order.order_id] = best_driver.driver_id
        
        return best_driver.driver_id
    
    async def process_concurrent_orders(self, orders: List[Order]) -> Dict[str, str]:
        """Process multiple orders concurrently (up to 3)"""
        # Process in batches of max_concurrent
        assignments = {}
        
        for i in range(0, len(orders), self.max_concurrent):
            batch = orders[i:i + self.max_concurrent]
            tasks = [self.assign_task(order) for order in batch]
            results = await asyncio.gather(*tasks)
            
            for order, driver_id in zip(batch, results):
                if driver_id:
                    assignments[order.order_id] = driver_id
        
        return assignments
    
    async def auto_reassign_pending(self) -> Dict[str, str]:
        """Automatically reassign pending orders when drivers become available"""
        if not self.pending_orders:
            return {}
        
        reassigned = {}
        orders_to_process = self.pending_orders[:self.max_concurrent]
        
        results = await self.process_concurrent_orders(orders_to_process)
        
        for order_id, driver_id in results.items():
            if driver_id:
                reassigned[order_id] = driver_id
                self.pending_orders = [o for o in self.pending_orders if o.order_id != order_id]
        
        return reassigned
    
    def complete_order(self, order_id: str):
        """Mark order as complete and free up driver capacity"""
        if order_id in self.assignments:
            driver_id = self.assignments[order_id]
            self.drivers[driver_id].active_orders -= 1
            del self.assignments[order_id]

# Example usage
async def main():
    # Initialize AI system
    ai = TaskAssignmentAI(max_concurrent_orders=3)
    
    # Add drivers
    drivers = [
        Driver("DRV001", (0, 0)),
        Driver("DRV002", (5, 5)),
        Driver("DRV003", (10, 10)),
        Driver("DRV004", (15, 15)),
    ]
    
    for driver in drivers:
        ai.add_driver(driver)
    
    # Create sample orders
    orders = [
        Order("ORD001", (2, 2), priority=1),
        Order("ORD002", (7, 7), priority=2),
        Order("ORD003", (12, 12), priority=1),
        Order("ORD004", (18, 18), priority=3),
        Order("ORD005", (3, 3), priority=2),
    ]
    
    # Process orders concurrently
    print("🚀 Processing orders with AI task assignment...")
    assignments = await ai.process_concurrent_orders(orders)
    
    print("\n✅ Assignments:")
    for order_id, driver_id in assignments.items():
        print(f"  {order_id} → {driver_id}")
    
    print(f"\n⏳ Pending orders: {len(ai.pending_orders)}")
    
    # Simulate completion and reassignment
    print("\n🔄 Completing ORD001...")
    ai.complete_order("ORD001")
    
    # Reassign pending orders
    reassigned = await ai.auto_reassign_pending()
    print(f"✅ Reassigned {len(reassigned)} pending orders")
    for order_id, driver_id in reassigned.items():
        print(f"  {order_id} → {driver_id}")

if __name__ == "__main__":
    asyncio.run(main())
