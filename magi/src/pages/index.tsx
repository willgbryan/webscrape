import BackgroundMedia from "@/components/ui/MediaBackground"
import '../app/globals.css';


export function MainPage() {
  return (
    <div className="w-full h-full flex justify-center items-center">
        <BackgroundMedia
          type="video"
          variant="light"
          src="https://openaicomproductionae4b.blob.core.windows.net/production-twill-01/c74791d0-75d2-48e6-acae-96d13bc97c56/paper-planes.mp4"
        />
    </div>
  )
}

export default MainPage;