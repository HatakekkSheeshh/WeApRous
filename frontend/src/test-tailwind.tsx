// Test component to verify Tailwind is working
// This should show a red box with white text if Tailwind is working
export default function TestTailwind() {
  return (
    <div className="bg-red-500 text-white p-4 rounded-lg">
      If you see this styled (red background, white text, rounded corners), Tailwind is working!
    </div>
  )
}

