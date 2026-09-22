import { test, expect, type Page } from '@playwright/test'

const workspaces = [
  ['Control tower', 'Delivery & stock exposure'],
  ['Transportation', 'Shipment risk monitor'],
  ['Inventory', 'Inventory exposure'],
  ['Demand', 'Demand planning'],
  ['Suppliers', 'Supplier reliability'],
  ['Production', 'Production capacity'],
  ['AI / ML insights', 'Data provenance & quality'],
  ['Scenario analysis', 'Planning assumptions'],
]

async function fitsPhone(page: Page) {
  await expect
    .poll(() => page.evaluate(() => document.documentElement.scrollWidth))
    .toBeLessThanOrEqual(page.viewportSize()!.width)
  // Hidden panel overflow can conceal broken controls even when the document fits.
  await expect
    .poll(() =>
      page.evaluate(() => {
        const width = document.documentElement.clientWidth
        return Array.from(
          document.querySelectorAll<HTMLElement>(
            'main button, main input, main select, .mini-metric, .model-meta > div, .confusion > *, .comparison-row > *, .recharts-wrapper, .drawer button',
          ),
        )
          .filter((element) => {
            if (element.closest('.table-wrap, .tabs:not(.scenario-tabs)')) return false
            const box = element.getBoundingClientRect()
            return box.width > 0 && (box.left < -1 || box.right > width + 1)
          })
          .map(
            (element) => element.getAttribute('aria-label') ?? element.className ?? element.tagName,
          )
      }),
    )
    .toEqual([])
}

async function navigate(page: Page, name: string) {
  await page.getByRole('button', { name: 'Open navigation' }).tap()
  const menu = page.getByRole('dialog', { name: 'Workspace navigation' })
  await expect(menu).toBeVisible()
  await menu.getByRole('button', { name, exact: true }).tap()
  await expect(menu).toBeHidden()
}

for (const width of [320, 340, 360, 390, 414]) {
  test.describe(`${width}px phone`, () => {
    test.use({ viewport: { width, height: 740 }, isMobile: true, hasTouch: true })

    test('all workspaces, model views and scenario results fit the screen', async ({ page }) => {
      test.setTimeout(90000)
      const errors: string[] = []
      page.on('pageerror', (error) => errors.push(error.message))
      await page.goto('/')
      for (const [name, heading] of workspaces) {
        await navigate(page, name)
        await expect(page.getByRole('heading', { name: heading, exact: true })).toBeVisible()
        await expect(page.locator('[aria-busy="true"]')).toHaveCount(0)
        await fitsPhone(page)
        for (const table of await page.getByRole('region').all()) {
          const sizes = await table.evaluate((el) => {
            el.scrollLeft = el.scrollWidth
            return { width: el.clientWidth, total: el.scrollWidth, scrolled: el.scrollLeft }
          })
          expect(sizes.total).toBeGreaterThan(sizes.width)
          expect(sizes.scrolled).toBeGreaterThan(0)
          await table.evaluate((el) => {
            el.scrollLeft = 0
          })
        }
        if (name === 'AI / ML insights') {
          for (const button of await page.locator('.model-tabs button').all()) {
            await button.tap()
            await fitsPhone(page)
          }
        }
      }
      await page.getByLabel('Demand change', { exact: true }).fill('30')
      await page.getByLabel('Additional replenishment (units)').fill('1000000')
      await page.getByRole('button', { name: 'Run inventory scenario' }).tap()
      await expect(page.getByText('Closing balance', { exact: true })).toBeVisible()
      await fitsPhone(page)
      await page.getByRole('button', { name: 'Transportation & cost', exact: true }).tap()
      await page.getByLabel('Distance (km)').fill('1500')
      await page.getByRole('button', { name: 'Run transport scenario' }).tap()
      await expect(page.getByText('PREDICTED FREIGHT COST', { exact: true })).toBeVisible()
      await fitsPhone(page)
      expect(errors).toEqual([])
      if (width <= 340)
        await page.screenshot({ path: `../test-results/scenario-${width}.png`, fullPage: true })
    })

    if (width <= 340) {
      test('touch drilldowns, definitions and navigation remain usable', async ({ page }) => {
        await page.goto('/')
        await page.getByRole('button', { name: 'About On-time delivery', exact: true }).tap()
        const definition = page.getByRole('tooltip')
        await expect(definition).toBeVisible()
        const box = await definition.boundingBox()
        expect(box!.x).toBeGreaterThanOrEqual(0)
        expect(box!.x + box!.width).toBeLessThanOrEqual(width)
        await page.getByRole('button', { name: 'About On-time delivery', exact: true }).tap()
        await expect(definition).toBeHidden()
        await page.locator('.exception-main').first().tap()
        await page.getByRole('button', { name: 'Mark reviewed', exact: true }).tap()
        await expect(page.getByRole('button', { name: 'Reviewed · undo' })).toBeVisible()
        await fitsPhone(page)
        await navigate(page, 'Transportation')
        await page.getByLabel('Risk level').selectOption('High')
        await page.getByLabel('Transport mode', { exact: true }).selectOption('ROAD')
        await page.locator('tbody .table-link').first().tap()
        await expect(page.getByRole('dialog')).toBeVisible()
        await expect(page.getByLabel('Close shipment')).toBeFocused()
        await expect.poll(() => page.evaluate(() => document.body.style.position)).toBe('fixed')
        await fitsPhone(page)
        await page.getByRole('button', { name: 'Compare a scenario' }).tap()
        await expect(page.getByRole('heading', { name: 'Transport assumptions' })).toBeVisible()
        await expect.poll(() => page.evaluate(() => document.body.style.position)).toBe('')
        await navigate(page, 'Demand')
        await page.getByLabel('Select demand product').selectOption({ index: 3 })
        await fitsPhone(page)
        await navigate(page, 'Inventory')
        await page.getByRole('button', { name: 'Stress-test this position' }).tap()
        await expect(
          page.getByRole('heading', { name: 'Planning assumptions', exact: true }),
        ).toBeVisible()
        await fitsPhone(page)
      })
    }
  })
}

test('short landscape viewport supports menu scrolling and dismissal', async ({ page }) => {
  await page.setViewportSize({ width: 568, height: 320 })
  await page.goto('/')
  const toggle = page.getByLabel('Open navigation')
  await toggle.click()
  await page.getByRole('dialog').getByRole('button', { name: 'Scenario analysis' }).click()
  await expect(
    page.getByRole('heading', { name: 'Planning assumptions', exact: true }),
  ).toBeVisible()
  await toggle.click()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toHaveCount(0)
  await expect(toggle).toBeFocused()
  await expect.poll(() => page.evaluate(() => document.body.style.position)).toBe('')
  await fitsPhone(page)
})
