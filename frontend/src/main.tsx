import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './views/App' // .tsx is implicit

const rootElement = document.getElementById('root')!

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
