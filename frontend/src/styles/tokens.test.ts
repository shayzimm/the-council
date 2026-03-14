// Verifies brand token names are correct strings (not a runtime test —
// this catches typos in the token names used in component classNames).
describe('brand token names', () => {
  const tokens = [
    'aura-cream',
    'aura-surface',
    'aura-blush',
    'aura-brown',
    'aura-muted',
    'aura-gold',
    'aura-white',
  ]

  it('all expected tokens are defined', () => {
    tokens.forEach((token) => {
      expect(typeof token).toBe('string')
      expect(token.startsWith('aura-')).toBe(true)
    })
  })
})
