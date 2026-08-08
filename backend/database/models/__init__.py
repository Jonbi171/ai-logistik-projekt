"""ORM model registry.

Importing this package registers every mapped table on ``Base.metadata``.
"""

from .base import Base
from .bill_of_materials import BillOfMaterials
from .inventory_balances import InventoryBalances
from .inventory_movements import InventoryMovements
from .inventory_snapshots import InventorySnapshots
from .locations import Locations
from .organizations import Organizations
from .product_suppliers import ProductSuppliers
from .production_capacity import ProductionCapacity
from .production_material_consumption import ProductionMaterialConsumption
from .production_orders import ProductionOrders
from .products import Products
from .purchase_order_lines import PurchaseOrderLines
from .purchase_orders import PurchaseOrders
from .sales_order_lines import SalesOrderLines
from .sales_orders import SalesOrders
from .shipment_events import ShipmentEvents
from .shipment_items import ShipmentItems
from .shipments import Shipments
from .transfer_order_lines import TransferOrderLines
from .transfer_orders import TransferOrders

__all__ = [
    "Base",
    "BillOfMaterials",
    "InventoryBalances",
    "InventoryMovements",
    "InventorySnapshots",
    "Locations",
    "Organizations",
    "ProductSuppliers",
    "ProductionCapacity",
    "ProductionMaterialConsumption",
    "ProductionOrders",
    "Products",
    "PurchaseOrderLines",
    "PurchaseOrders",
    "SalesOrderLines",
    "SalesOrders",
    "ShipmentEvents",
    "ShipmentItems",
    "Shipments",
    "TransferOrderLines",
    "TransferOrders",
]
