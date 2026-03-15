import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { TopNav } from './TopNav'

const renderTopNav = (onHamburgerClick = () => {}) =>
  render(
    <MemoryRouter>
      <TopNav onHamburgerClick={onHamburgerClick} />
    </MemoryRouter>
  )

describe('TopNav', () => {
  it('renders the AURA wordmark', () => {
    renderTopNav()
    expect(screen.getByText('AURA')).toBeInTheDocument()
  })

  it('renders desktop nav links', () => {
    renderTopNav()
    expect(screen.getByRole('link', { name: 'Home' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Council' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Progress' })).toBeInTheDocument()
  })

  it('calls onHamburgerClick when hamburger button is pressed', async () => {
    const handler = vi.fn()
    renderTopNav(handler)
    screen.getByRole('button', { name: /menu/i }).click()
    expect(handler).toHaveBeenCalledTimes(1)
  })
})
