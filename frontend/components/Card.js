import { forwardRef } from 'react'
import { motion } from 'framer-motion'
import { DocumentIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'

const Card = forwardRef(({ className = '', children, hover = true, ...props }, ref) => {
  const Component = hover ? motion.div : 'div'
  
  return (
    <Component
      ref={ref}
      className={`bg-white rounded-xl shadow-sm border border-secondary-200 ${className}`}
      whileHover={hover ? { y: -2, boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.15)' } : undefined}
      transition={{ duration: 0.2 }}
      {...props}
    >
      {children}
    </Component>
  )
})

Card.displayName = 'Card'

export const DocumentCard = ({ document, status = 'ready', size, onRemove }) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'ready':
        return <CheckCircleIcon className="h-4 w-4 text-success-500" />
      case 'processing':
        return <div className="h-4 w-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      case 'error':
        return <ExclamationTriangleIcon className="h-4 w-4 text-danger-500" />
      default:
        return <CheckCircleIcon className="h-4 w-4 text-success-500" />
    }
  }

  const getStatusColor = () => {
    switch (status) {
      case 'ready':
        return 'text-success-700 bg-success-50'
      case 'processing':
        return 'text-primary-700 bg-primary-50'
      case 'error':
        return 'text-danger-700 bg-danger-50'
      default:
        return 'text-success-700 bg-success-50'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="group relative"
    >
      <Card className="p-3 hover:shadow-md transition-all duration-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 min-w-0 flex-1">
            <div className="flex-shrink-0">
              <DocumentIcon className="h-5 w-5 text-secondary-400" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-secondary-900 truncate" title={document}>
                {document}
              </p>
              {size && (
                <p className="text-xs text-secondary-500 mt-0.5">
                  {(size / (1024 * 1024)).toFixed(1)} MB
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor()}`}>
              {getStatusIcon()}
              <span className="capitalize">{status}</span>
            </span>
            {onRemove && (
              <button
                onClick={() => onRemove(document)}
                className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 p-1 rounded-full hover:bg-secondary-100"
                title="Remove document"
              >
                <svg className="h-4 w-4 text-secondary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  )
}

export default Card
