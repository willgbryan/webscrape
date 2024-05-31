import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import '../app/globals.css';
import { SparklesCore } from "@/components/ui/Sparkles";
import { GradientHeading } from "@/components/ui/GradientHeading";
import { TextureCardContent, TextureCardHeader, TextureCardStyled } from "@/components/ui/TextureCard";
import { AnimatedNumber } from "@/components/ui/NumberAnimations";
import { submitScrapeRequest, WebSocketManager } from "@/services/api";

function CollectionExample({ setNumColumns, setNumRows, numColumns, numRows, showDetails, setShowDetails }) {
    const [scrapeTopic, setScrapeTopic] = useState('');
    const [columns, setColumns] = useState('');
    const [websocketManager] = useState(new WebSocketManager());

    const handleScrapeTopicChange = (e) => {
        setScrapeTopic(e.target.value);
    };

    const handleColumnsChange = (e) => {
        const value = e.target.value;
        setColumns(value);

        if (!showDetails && value.length > 0) {
            setShowDetails(true);
        }

        const rowCountMatch = value.match(/row count:\s*(\d+)/i);
        const rowCount = rowCountMatch ? parseInt(rowCountMatch[1], 10) : 0;
        const columnsCount = value.split(',').map(v => v.trim()).filter(v => v !== '' && !v.toLowerCase().startsWith('row count:')).length;

        setNumRows(rowCount);
        setNumColumns(columnsCount);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            const data = await submitScrapeRequest(scrapeTopic, columns.split(','));
            console.log('Form submitted successfully', data);
            // Connect to WebSocket and handle real-time updates
            websocketManager.connect('ws://localhost:8000/ws', (data) => {
                console.log('WebSocket message received:', data);
                handleWebSocketMessage(data);
            }, (error) => {
                console.error('WebSocket error:', error);
            });
        } catch (error) {
            console.error('Error submitting form:', error);
        }
    };

    const handleWebSocketMessage = (data) => {
        console.log("Received data of type:", data.type);
        let accumulatedData = '';

        if (data.type === 'logs') {
          addAgentResponse(data);
        } else if (data.type === 'report') {
          accumulatedData += data.output;
        //   writeReport(data);
        }
      };

      const addAgentResponse = (data) => {
        const output = document.getElementById("output");
        output.innerHTML += '<div class="agent_response">' + data.output + '</div>';
        output.scrollTop = output.scrollHeight;
        output.style.display = "block";
      };

      const writeReport = (data) => {
        // Implement your logic to handle report
      };

    return (
        <div className="w-full lg:grid lg:min-h-[600px] lg:grid-cols-2 xl:min-h-[800px]">
            <div className="flex items-center justify-center py-12">
                <form className="mx-auto grid w-[350px] gap-6" onSubmit={handleSubmit}>
                    <div className="grid gap-2 text-center">
                        <h1 className="text-3xl font-bold">Magi</h1>
                        <p className="text-balance text-muted-foreground">
                            Webscraping like you would not believe.
                        </p>
                    </div>
                    <div className="grid gap-4">
                        <div className="grid gap-2">
                            <Label htmlFor="prompt">Scrape Topic</Label>
                            <Input
                                id="prompt"
                                type="text"
                                placeholder="Austin VC Firms"
                                value={scrapeTopic}
                                onChange={handleScrapeTopicChange}
                                required
                            />
                        </div>
                        <div className="grid gap-2">
                            <div className="flex items-center">
                                <Label htmlFor="columns">Columns</Label>
                            </div>
                            <Input 
                                id="columns" 
                                type="text" 
                                placeholder="firm name, fund size, row count: 10"
                                value={columns}
                                onChange={handleColumnsChange}
                                required 
                            />
                        </div>
                        <Button type="submit" className="w-full">
                            Curate
                        </Button>
                    </div>
                </form>
            </div>
            <div className="relative hidden bg-muted lg:block">
                <div className="h-[56rem] w-full bg-black flex flex-col items-center justify-center overflow-hidden rounded-md">
                    {showDetails && (
                    <div>
                        <div className="flex flex-col sm:flex-row gap-2 p-4 transition-opacity duration-500 opacity-0 animate-fade-in">
                            <PrecisionExample numColumns={numColumns} />
                            <FormatExample numRows={numRows} />
                            <CostExample numColumns={numColumns} numRows={numRows} />
                        </div>
                    
                    <div className="w-[40rem] h-40 relative">
                        {/* Gradients */}
                        <div className="absolute inset-x-20 top-0 bg-gradient-to-r from-transparent via-indigo-500 to-transparent h-[2px] w-3/4 blur-sm" />
                        <div className="absolute inset-x-20 top-0 bg-gradient-to-r from-transparent via-indigo-500 to-transparent h-px w-3/4" />
                        <div className="absolute inset-x-60 top-0 bg-gradient-to-r from-transparent via-sky-500 to-transparent h-[5px] w-1/4 blur-sm" />
                        <div className="absolute inset-x-60 top-0 bg-gradient-to-r from-transparent via-sky-500 to-transparent h-px w-1/4" />
                    
                        {/* Core component */}
                        <SparklesCore
                            background="transparent"
                            minSize={0.4}
                            maxSize={1}
                            particleDensity={Math.min(numRows, 4000)}  // Increase particle density with numRows, with a ceiling of 10000
                            className="w-full h-full"
                            particleColor="#FFFFFF"
                        />
                    
                        {/* Radial Gradient to prevent sharp edges */}
                        <div className="absolute inset-0 w-full h-full bg-black [mask-image:radial-gradient(350px_200px_at_top,transparent_20%,white)]"></div>
                    </div>
                    </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function PrecisionExample({ numColumns }) {
    return (
        <TextureCardStyled>
            <TextureCardHeader className="text-center">
                <GradientHeading variant="light" size="sm">Columns</GradientHeading>
            </TextureCardHeader>
            <TextureCardContent>
                    <div
                        className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-sky-500 to-indigo-500"
                        style={{ minWidth: "150px", textAlign: "center" }}
                    >
                        <AnimatedNumber value={numColumns} precision={0} />
                    </div>
            </TextureCardContent>
        </TextureCardStyled>
    )
}

function FormatExample({ numRows }) {
    return (
        <TextureCardStyled>
            <TextureCardHeader className="text-center">
                <GradientHeading variant="light" size="sm">Rows</GradientHeading>
            </TextureCardHeader>
            <TextureCardContent>
                    <div
                        className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-sky-500 to-indigo-500"
                        style={{ minWidth: "150px", textAlign: "center" }}
                    >
                        <AnimatedNumber value={numRows} precision={0} />
                    </div>
            </TextureCardContent>
        </TextureCardStyled>
    )
}

function CostExample({ numColumns, numRows }) {
    const cost = numColumns * numRows * 0.015

    return (
        <TextureCardStyled>
            <TextureCardHeader className="text-center">
                <GradientHeading variant="light" size="sm">Cost</GradientHeading>
            </TextureCardHeader>
            <TextureCardContent>
                <div className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-sky-500 to-indigo-500" style={{ minWidth: "150px", textAlign: "center" }}>
                    <AnimatedNumber value={cost} precision={2} />
                </div>
            </TextureCardContent>
        </TextureCardStyled>
    )
}

function OgImageSection() {
    const [numColumns, setNumColumns] = useState(0)
    const [numRows, setNumRows] = useState(0)
    const [showDetails, setShowDetails] = useState(false)

    return (
        <div className="w-full flex flex-col gap-2 justify-between pt-6">
            <CollectionExample setNumColumns={setNumColumns} setNumRows={setNumRows} numColumns={numColumns} numRows={numRows} showDetails={showDetails} setShowDetails={setShowDetails} />
        </div>
    )
}

export function Dashboard() {
    return (
        <OgImageSection />
    )
}

export default Dashboard;
