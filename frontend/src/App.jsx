import { useState } from 'react'

function App() {
  const [month, setMonth] = useState('09')
  return (
    <div style={{padding:'1rem', fontFamily:'sans-serif'}}>
      <h1>Finance Assistant (Placeholder)</h1>
      <label>Month: 
        <select value={month} onChange={e=>setMonth(e.target.value)}>
          {Array.from({length:12}, (_,i)=> String(i+1).padStart(2,'0')).map(m=> <option key={m} value={m}>{m}</option>)}
        </select>
      </label>
      <p>Frontend scaffold ready. Implement components next.</p>
    </div>
  )
}
export default App
