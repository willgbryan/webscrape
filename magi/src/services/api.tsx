const baseURL = process.env.NEXT_PUBLIC_BACKEND_URL;

export class WebSocketManager {
    websocket: WebSocket | null = null;
  
    connect(url: string, onMessage: (data: any) => void, onError: (error: any) => void) {
      this.websocket = new WebSocket(url);
  
      this.websocket.onopen = () => {
        console.log('WebSocket connection opened');
      };
  
      this.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onMessage(data);
      };
  
      this.websocket.onerror = (event) => {
        console.error('WebSocket error:', event);
        onError(event);
      };
  
      this.websocket.onclose = () => {
        console.log('WebSocket connection closed');
      };
    }
  
    sendMessage(message: string) {
      if (this.websocket) {
        this.websocket.send(message);
      }
    }
  
    disconnect() {
      if (this.websocket) {
        this.websocket.close();
      }
    }
  }
  
  export async function submitForm(formData: any) {
    try {
      const response = await fetch(`${baseURL}/ws`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
  
      if (response.ok) {
        return await response.json();
      } else {
        throw new Error('Form submission failed');
      }
    } catch (error) {
      console.error('Error submitting form:', error);
      throw error;
    }
  }
  