import GalleryNameDialog from './GalleryNameDialog'

interface Props {
  count: number
  onSave: (name: string) => void
  onCancel: () => void
}

export default function SaveAsNewGalleryDialog({ count, onSave, onCancel }: Props) {
  return (
    <GalleryNameDialog
      isOpen={true}
      defaultName={`Selection (${count})`}
      onSubmit={onSave}
      onCancel={onCancel}
    />
  )
}
