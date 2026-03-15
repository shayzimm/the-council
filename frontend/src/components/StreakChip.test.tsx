import { render, screen } from '@testing-library/react'
import { StreakChip } from './StreakChip'

describe('StreakChip', () => {
  it('renders habit label and day count', () => {
    render(<StreakChip label="Training" days={12} />)
    expect(screen.getByText('Training')).toBeInTheDocument()
    expect(screen.getByText('12d')).toBeInTheDocument()
  })
})
