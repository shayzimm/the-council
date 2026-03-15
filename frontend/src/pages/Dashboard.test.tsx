import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Dashboard from './Dashboard'

const renderDashboard = () =>
  render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>
  )

describe('Dashboard', () => {
  it('renders the greeting', () => {
    renderDashboard()
    expect(screen.getByText(/Good morning, Shay/i)).toBeInTheDocument()
  })

  it('renders the check-in prompt', () => {
    renderDashboard()
    expect(screen.getByText(/Morning check-in/i)).toBeInTheDocument()
  })

  it('renders Whoop snapshot section', () => {
    renderDashboard()
    expect(screen.getByText('Recovery')).toBeInTheDocument()
    expect(screen.getByText('HRV')).toBeInTheDocument()
    expect(screen.getByText('Sleep')).toBeInTheDocument()
  })

  it("renders today's tasks", () => {
    renderDashboard()
    expect(screen.getByText(/Upper body/i)).toBeInTheDocument()
    expect(screen.getByText(/Tret night/i)).toBeInTheDocument()
    expect(screen.getByText(/NSDR/i)).toBeInTheDocument()
  })

  it('renders active streaks', () => {
    renderDashboard()
    expect(screen.getByText('Training')).toBeInTheDocument()
  })

  it('renders quick access links to Council', () => {
    renderDashboard()
    expect(screen.getAllByRole('link', { name: /Rex|Sage|Celeste|Council/i }).length).toBeGreaterThan(0)
  })

  it('renders this week at a glance section', () => {
    renderDashboard()
    expect(screen.getByText(/this week/i)).toBeInTheDocument()
  })
})
