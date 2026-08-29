const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '')

const endpoint = (path: string) => `${API_BASE_URL}${path}`

export const API_ENDPOINTS = {
  currentInventory: endpoint('/current-inventory'),
  shipmentOverview: endpoint('/shipment-overview'),
  salesOrderOverview: endpoint('/sales-order-overview'),
  purchaseOrderOverview: endpoint('/purchase-order-overview'),
  inventoryHistory: endpoint('/inventory-history'),
  productBom: endpoint('/product-bom'),
  productSupplierOverview: endpoint('/product-supplier-overview'),
  shipmentEvents: endpoint('/shipment-events'),
  productSuppliers: endpoint('/product-suppliers'),
  productSuppliersOrderCost: endpoint('/product-suppliers-order-cost'),
  
} as const

export type ApiEndpoint = (typeof API_ENDPOINTS)[keyof typeof API_ENDPOINTS]
