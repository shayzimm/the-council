import { render, screen } from '@testing-library/react'
import { StatPill } from './StatPill'

describe('StatPill', () => {
  it('renders value and label', () => {
    render(<StatPill label="Recovery" value={74} unit="%" />)
    expect(screen.getByText('74%')).toBeInTheDocument()
    expect(screen.getByText('Recovery')).toBeInTheDocument()
  })

  it('renders without a unit', () => {
    render(<StatPill label="HRV" value="62ms" />)
    expect(screen.getByText('62ms')).toBeInTheDocument()
  })
})
