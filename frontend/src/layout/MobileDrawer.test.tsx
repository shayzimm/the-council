import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { MobileDrawer } from './MobileDrawer'

const renderDrawer = (isOpen: boolean, onClose = () => {}) =>
  render(
    <MemoryRouter>
      <MobileDrawer isOpen={isOpen} onClose={onClose} />
    </MemoryRouter>
  )

describe('MobileDrawer', () => {
  it('does not show nav links when closed', () => {
    renderDrawer(false)
    expect(screen.queryByRole('link', { name: 'Home' })).not.toBeVisible()
  })

  it('shows nav links when open', () => {
    renderDrawer(true)
    expect(screen.getByRole('link', { name: 'Home' })).toBeVisible()
    expect(screen.getByRole('link', { name: 'Council' })).toBeVisible()
  })

  it('calls onClose when backdrop is clicked', async () => {
    const handler = vi.fn()
    renderDrawer(true, handler)
    await userEvent.click(screen.getByRole('presentation'))
    expect(handler).toHaveBeenCalledTimes(1)
  })
})
