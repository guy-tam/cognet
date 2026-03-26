'use client'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function SearchRedirect() {
  const router = useRouter()
  useEffect(() => { router.replace('/en/discover') }, [router])
  return <p>Redirecting...</p>
}
