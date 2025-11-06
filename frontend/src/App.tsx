import KeyboardPage from './pages/KeyboardPage'

function App() {
  return (
    <div className="min-h-screen bg-black text-white flex flex-col overflow-hidden">
      <header className="px-6 py-4 border-b border-white/20 flex-shrink-0">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-white text-center">
            Indic AutoComplete
          </h1>
          <p className="text-center text-gray-400 text-sm mt-1">
            Multilingual typing assistant
          </p>
        </div>
      </header>
      <main className="flex-1 flex items-center justify-center w-full px-4 py-6 overflow-auto">
        <KeyboardPage />
      </main>
      <footer className="px-6 py-2 border-t border-white/20 flex-shrink-0">
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-3 text-xs text-gray-400">
          <span>v2.0</span>
          <span>•</span>
          <span>5 Languages</span>
          <span>•</span>
          <span>AI-Powered</span>
        </div>
      </footer>
    </div>
  )
}

export default App
