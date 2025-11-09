import KeyboardPage from './pages/KeyboardPage'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-slate-900 to-cyan-950 text-white flex flex-col overflow-hidden">
      <header className="px-6 py-6 flex-shrink-0 backdrop-blur-sm bg-white/5">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent text-center">
            Indic AutoComplete
          </h1>
        </div>
      </header>
      <main className="flex-1 flex items-center justify-center w-full px-4 py-8 overflow-auto">
        <KeyboardPage />
      </main>
    </div>
  )
}

export default App

