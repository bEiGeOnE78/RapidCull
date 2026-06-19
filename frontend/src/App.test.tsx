import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
}

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />, { wrapper })
    expect(screen.getByText('People')).toBeInTheDocument()
  })
})
