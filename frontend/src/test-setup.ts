import '@testing-library/jest-dom'

// jsdom does not propagate the `inert` HTML attribute to getComputedStyle, so
// jest-dom's toBeVisible() stays true even for inert subtrees.
//
// Patch: return opacity:'0' for any element whose nearest ancestor (or itself)
// carries the [inert] attribute.  This makes toBeVisible() return false while
// leaving queryByRole unaffected (it only checks display/visibility, not
// opacity).
const _getComputedStyle = window.getComputedStyle.bind(window)
window.getComputedStyle = (elt: Element, pseudo?: string | null) => {
  const style = _getComputedStyle(elt, pseudo)
  let node: Element | null = elt
  while (node) {
    if (node.hasAttribute('inert')) {
      return new Proxy(style, {
        get(target, prop) {
          if (prop === 'opacity') return '0'
          const val = (target as unknown as Record<string | symbol, unknown>)[prop]
          return typeof val === 'function' ? val.bind(target) : val
        },
      })
    }
    node = node.parentElement
  }
  return style
}
