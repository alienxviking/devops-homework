import { useState } from 'react'

export default function App() {
  const [count, setCount] = useState(0)

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', textAlign: 'center', marginTop: 120 }}>
      <h1 style={{ color: '#149eca' }}>Hello World from React!</h1>
      <p>React (Vite build) served by Nginx inside a Docker container</p>
      <button onClick={() => setCount(count + 1)} style={{ padding: '8px 16px', fontSize: 16 }}>
        clicked {count} times
      </button>
    </div>
  )
}
