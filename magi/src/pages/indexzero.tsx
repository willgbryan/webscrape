"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import FamilyButton from "@/components/ui/FamilyButton"
import BackgroundMedia from "@/components/ui/MediaBackground"
import { AnimatedNumber } from "@/components/ui/NumberAnimations"
import { GradientHeading } from "@/components/ui/GradientHeading"
import {
  TextureCardContent,
  TextureCardHeader,
  TextureCardStyled,
} from "@/components/ui/TextureCard"

import '../app/globals.css';
import { toast } from "sonner"
import { Minus, Plus } from "lucide-react"

// Updated CollectionExample with new functionality
function CollectionExample({ setNumColumns, setNumRows }) {
  const handleInputChange = (e) => {
    const value = e.target.value

    // Extract row count
    const rowCountMatch = value.match(/row count:\s*(\d+)/i)
    const rowCount = rowCountMatch ? parseInt(rowCountMatch[1], 10) : 0

    // Extract columns
    const columns = value.split(',').map(v => v.trim()).filter(v => v !== '' && !v.toLowerCase().startsWith('row count:')).length

    setNumRows(rowCount)
    setNumColumns(columns)
  }

  return (
    <TextureCardStyled className="w-full">
      <TextureCardHeader className="px-3">
        <GradientHeading variant="light" size="sm">What would you like to collect?</GradientHeading>
      </TextureCardHeader>
      <TextureCardContent className="flex flex-col gap-4">
        <Textarea placeholder="Type your message here." onChange={handleInputChange} className="bg-transparent text-white placeholder:text-gray border-white/10 border shadow-lg" />
        <Input type="text" placeholder="column 1, column 2, column 3, row count: 500" onChange={handleInputChange} className="bg-transparent text-white placeholder:text-gray border-white/10 border shadow-lg" />
      </TextureCardContent>
    </TextureCardStyled>
  )
}

// Updated PrecisionExample
function PrecisionExample({ numColumns }) {
  return (
    <TextureCardStyled>
      <TextureCardHeader className="pl-3">
        <GradientHeading variant="light" size="xs">Columns</GradientHeading>
      </TextureCardHeader>
      <TextureCardContent>
        <div className="flex gap-2">
          <div
            className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-neutral-200 to-[#ff7300]"
            style={{ minWidth: "80px", textAlign: "left" }}
          >
            <AnimatedNumber value={numColumns} precision={0} />
          </div>
        </div>
      </TextureCardContent>
    </TextureCardStyled>
  )
}

// Updated FormatExample to display the row count
function FormatExample({ numRows }) {
  return (
    <TextureCardStyled>
      <TextureCardHeader className="pl-3">
        <GradientHeading variant="light" size="xs">Rows</GradientHeading>
      </TextureCardHeader>
      <TextureCardContent>
        <div className="flex gap-2">
          <div
            className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-neutral-200 to-[#ff7300]"
            style={{ minWidth: "80px", textAlign: "left" }}
          >
            <AnimatedNumber value={numRows} precision={0} />
          </div>
        </div>
      </TextureCardContent>
    </TextureCardStyled>
  )
}

// Updated CostExample
function CostExample({ numColumns, numRows }) {
  const cost = numColumns * numRows * 0.015

  return (
    <TextureCardStyled>
      <TextureCardHeader className="pl-3">
        <GradientHeading variant="light" size="xs">Cost</GradientHeading>
      </TextureCardHeader>
      <TextureCardContent>
        <div className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-neutral-200 to-[#ff7300]" style={{ minWidth: "50px", textAlign: "left" }}>
          <AnimatedNumber value={cost} precision={2} />
        </div>
      </TextureCardContent>
    </TextureCardStyled>
  )
}

export function OgImageSection() {
  const [numColumns, setNumColumns] = useState(0)
  const [numRows, setNumRows] = useState(0)

  return (
    <div className="w-full flex flex-col gap-2 justify-between pt-6">
      <CollectionExample setNumColumns={setNumColumns} setNumRows={setNumRows} />
      <div className="flex flex-col sm:flex-row gap-2">
        <PrecisionExample numColumns={numColumns} />
        <FormatExample numRows={numRows} />
        <CostExample numColumns={numColumns} numRows={numRows} />
      </div>
    </div>
  )
}

export function MainPage() {
  return (
    <div className="relative w-full h-full flex justify-center items-center">
      <BackgroundMedia
        type="video"
        variant="light"
        src="https://videos.pexels.com/video-files/15364192/15364192-hd_1280_720_30fps.mp4"
      />
      <div className="absolute bottom-4 right-4">
        <FamilyButton>
          <OgImageSection />
        </FamilyButton>
      </div>
    </div>
  )
}

export default MainPage
