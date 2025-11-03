declare module 'epubjs' {
  export default function Epub(url: string): EpubBook

  export interface EpubBook {
    renderTo(element: HTMLElement, options: RenditionOptions): Rendition
    ready: Promise<void>
  }

  export interface RenditionOptions {
    width?: string | number
    height?: string | number
    spread?: 'none' | 'always'
  }

  export interface Rendition {
    display(target?: string | number): Promise<void>
    destroy(): void
    currentLocation(): {
      start?: {
        displayed?: {
          page?: number
        }
      }
    }
  }
}

