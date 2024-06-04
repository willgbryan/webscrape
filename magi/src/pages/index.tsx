import { useState, ChangeEvent, FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import '../app/globals.css';
import { SparklesCore } from "@/components/ui/Sparkles";
import { GradientHeading } from "@/components/ui/GradientHeading";
import { TextureCardContent, TextureCardHeader, TextureCardStyled } from "@/components/ui/TextureCard";
import { AnimatedNumber } from "@/components/ui/NumberAnimations";
import { DataTableDemo } from "@/components/ui/DataTable";

interface CollectionExampleProps {
    setNumColumns: (numColumns: number) => void;
    setNumRows: (numRows: number) => void;
    numColumns: number;
    numRows: number;
    showDetails: boolean;
    setShowDetails: (showDetails: boolean) => void;
}

function CollectionExample({ setNumColumns, setNumRows, numColumns, numRows, showDetails, setShowDetails }: CollectionExampleProps) {
    const [scrapeTopic, setScrapeTopic] = useState('');
    const [columns, setColumns] = useState('');
    const [dataset, setDataset] = useState<Record<string, any>>({});
    const datasetArray = Object.values(dataset);


    // const [dataset, setDataset] = useState<any[]>([]); // State to hold the dataset

    const handleScrapeTopicChange = (e: ChangeEvent<HTMLInputElement>) => {
        setScrapeTopic(e.target.value);
    };

    const handleColumnsChange = (e: ChangeEvent<HTMLInputElement>) => {
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

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setShowDetails(false); // Hide details when "Curate" is clicked
        console.log('Good submit')
        try {
            listenToSockEvents();
        } catch (error) {
            console.error('Error submitting form:', error);
        }
    };

    const log = (level: 'info' | 'warn' | 'error', message: string): void => {
        if (console[level]) {
            console[level](`[${level.toUpperCase()}] ${message}`);
        } else {
            console.log(`[LOG] ${message}`);
        }
    };

    const listenToSockEvents = () => {
        const { protocol, host } = window.location;
        const ws_uri = `${protocol === 'https:' ? 'wss:' : 'ws:'}//localhost:8000/ws`;
        const socket = new WebSocket(ws_uri);

        log('info', 'Connecting to WebSocket...');

        socket.onopen = () => {
            log('info', 'WebSocket connection opened');

            const taskInput = document.querySelector('#prompt') as HTMLInputElement;
            if (!taskInput) {
                log('error', 'Task input not found');
                return;
            }

            const columnsInput = document.querySelector('#columns') as HTMLInputElement;
            if(!columnsInput) {
                log('error', 'Columns input not found');
                return;
            }
            const columnsValue = columnsInput.value;

            const columnHeaders = columnsValue.split(',')
                                .map(v => v.trim())
                                .filter(v => v !== '' && !v.toLowerCase().startsWith('row count:'))
                                .join(', ');
            console.log(`Column headers: ${columnHeaders}`)

            const rowCountMatch = columnsValue.match(/row count:\s*(\d+)/i);
            const rowCount = rowCountMatch ? parseInt(rowCountMatch[1], 10) : 0;
            console.log(`Row count: ${rowCount}`)

            if(!columnHeaders) {
                log('error', 'No column headers provided');
                return;
            }

            const task = taskInput.value;
            log('info', `Task: ${task}`);

            const requestData = { task, columnHeaders, rowCount };
            log('info', `Request data: ${JSON.stringify(requestData)}`);

            socket.send(`start ${JSON.stringify(requestData)}`);
        };

        socket.onmessage = (event) => {
            log('info', 'WebSocket message received');
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'row_update') {
                    setDataset(prevDataset => {
                        const existingRow = prevDataset[data.id];
                        if (existingRow) {
                            return { ...prevDataset, [data.id]: { ...existingRow, ...data.output } };
                        } else {
                            return { ...prevDataset, [data.id]: data.output };
                        }
                    });
                }
                // log('info', `Received data of type: ${data.type}`);
                // if (data.type === 'dataset') {
                //     const parsedData = JSON.parse(data.output); // Ensure the data is parsed correctly
                //     setDataset(parsedData); // Set the dataset state
                // }
            } catch (error) {
                log('error', `Error processing message: ${error}`);
            }
        };

        socket.onerror = (event: Event) => {
            log('error', `WebSocket error: ${JSON.stringify(event)}`);
        };

        socket.onclose = (event: CloseEvent) => {
            log('info', `WebSocket closed: ${event.code}`);
        };
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
                    {showDetails ? (
                        <div>
                            <div className={'flex flex-col sm:flex-row gap-2 p-4 transition-opacity duration-500 opacity-0 animate-fade-in'}>
                                <PrecisionExample numColumns={numColumns} />
                                <FormatExample numRows={numRows} />
                                <CostExample numColumns={numColumns} numRows={numRows} />
                            </div>
                        
                            <div className="w-[40rem] h-40 relative">
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
                    ) : datasetArray.length > 0 && (
                        <DataTableDemo data={datasetArray} />
                    )}
                </div>
            </div>
        </div>
    );
}

interface PrecisionExampleProps {
    numColumns: number;
}

function PrecisionExample({ numColumns }: PrecisionExampleProps) {
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

interface FormatExampleProps {
    numRows: number;
}

function FormatExample({ numRows }: FormatExampleProps) {
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

interface CostExampleProps {
    numColumns: number;
    numRows: number;
}

function CostExample({ numColumns, numRows }: CostExampleProps) {
    const cost = numColumns * numRows * 0.015;

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

interface OgImageSectionProps {
    dataset: any[];
}

function OgImageSection() {
    const [numColumns, setNumColumns] = useState(0);
    const [numRows, setNumRows] = useState(0);
    const [showDetails, setShowDetails] = useState(false);

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
