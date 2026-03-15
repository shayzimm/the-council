interface PageWrapperProps {
  children: React.ReactNode
}

export function PageWrapper({ children }: PageWrapperProps) {
  return (
    <main className="max-w-screen-lg mx-auto px-4 py-8 w-full">
      {children}
    </main>
  )
}
