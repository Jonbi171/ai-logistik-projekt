import { test, expect } from '@playwright/test'

test('all eight workspaces render data without browser errors', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Delivery & stock exposure' })).toBeVisible()
  await expect(page.getByText('65.9').first()).toBeVisible()
  await page.screenshot({ path: '../test-results/control-tower-desktop.png', fullPage: true })
  for (const [name, heading] of [
    ['Transportation', 'Shipment risk monitor'],
    ['Inventory', 'Inventory exposure'],
    ['Demand', 'Demand planning'],
    ['Suppliers', 'Supplier reliability'],
    ['Production', 'Production capacity'],
    ['AI / ML insights', 'Data provenance & quality'],
    ['Scenario analysis', 'Planning assumptions'],
  ]) {
    await page.getByRole('navigation').getByRole('button', { name, exact: true }).click()
    await expect(page.getByRole('heading', { name: heading, exact: true })).toBeVisible()
    await expect(page.getByText('Unable to load this view')).toHaveCount(0)
  }
  expect(errors).toEqual([])
})

test('shipment filters, evidence and scenario deep link work', async ({ page }) => {
  await page.goto('/#Transportation')
  await page.getByLabel('Risk level').selectOption('High')
  await page.getByLabel('Transport mode', { exact: true }).selectOption('ROAD')
  await expect(page.locator('tbody tr').first()).toBeVisible()
  const name = await page.locator('tbody .table-link').first().innerText()
  await page.locator('tbody .table-link').first().click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await expect(page.getByRole('heading', { name, exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Compare a scenario' }).click()
  await expect(page.getByRole('heading', { name: 'Transport assumptions' })).toBeVisible()
  await page.getByRole('button', { name: 'Run transport scenario' }).click()
  await expect(page.getByText('PREDICTED FREIGHT COST', { exact: true })).toBeVisible()
  await page.getByLabel('Distance (km)').fill('1500')
  await expect(page.getByText('PREDICTED FREIGHT COST', { exact: true })).toHaveCount(0)
  await page.getByRole('button', { name: 'Run transport scenario' }).click()
  await expect(page.getByText('PREDICTED FREIGHT COST', { exact: true })).toBeVisible()
  await page.screenshot({ path: '../test-results/transport-scenario.png', fullPage: true })
})

test('inventory scenario, demand selection and model comparisons work', async ({ page }) => {
  await page.goto('/#Inventory')
  await page.getByRole('button', { name: 'Stress-test this position' }).click()
  await expect(
    page.getByRole('heading', { name: 'Planning assumptions', exact: true }),
  ).toBeVisible()
  await page.getByLabel('Demand change', { exact: true }).fill('30')
  await page.getByRole('button', { name: 'Run inventory scenario' }).click()
  await expect(page.getByText('Closing balance', { exact: true })).toBeVisible()
  await page.screenshot({ path: '../test-results/inventory-scenario.png', fullPage: true })
  await page.getByRole('navigation').getByRole('button', { name: 'Demand', exact: true }).click()
  await expect(page.getByLabel('Select demand product')).toBeVisible()
  await page.getByLabel('Select demand product').selectOption({ index: 3 })
  await expect(page.getByText('Next 4 weeks', { exact: true }).first()).toBeVisible()
  await page
    .getByRole('navigation')
    .getByRole('button', { name: 'AI / ML insights', exact: true })
    .click()
  await page.getByRole('button', { name: 'Freight cost LinearRegression' }).click()
  await expect(page.getByRole('heading', { name: 'Model comparison', exact: true })).toBeVisible()
  await page.screenshot({ path: '../test-results/model-insights.png', fullPage: true })
})

test('exception review persists locally', async ({ page }) => {
  await page.goto('/')
  await page.locator('.exception-main').first().click()
  await page.getByRole('button', { name: 'Mark reviewed', exact: true }).click()
  await page.reload()
  await page.locator('.exception-main').first().click()
  await expect(page.getByRole('button', { name: 'Reviewed · undo' })).toBeVisible()
})

test('mobile navigation and layout remain usable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Control tower', exact: true })).toBeVisible()
  await page.getByLabel('Open navigation').click()
  await page.getByRole('navigation').getByRole('button', { name: 'Inventory', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Inventory exposure' })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(391)
  await page.screenshot({ path: '../test-results/inventory-mobile.png', fullPage: true })
})

test('API failure shows a retryable state', async ({ page }) => {
  await page.route('**/api/tower/overview', (route) =>
    route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Test connection interruption' }),
    }),
  )
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Unable to load this view' })).toBeVisible()
  await page.unroute('**/api/tower/overview')
  await page.getByRole('button', { name: 'Try again' }).click()
  await expect(page.getByRole('heading', { name: 'Delivery & stock exposure' })).toBeVisible()
})
