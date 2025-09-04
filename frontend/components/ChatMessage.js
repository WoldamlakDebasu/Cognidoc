import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism'
import { DocumentIcon, ClockIcon, CheckCircleIcon } from '@heroicons/react/24/outline'

export default function ChatMessage({ 
  message, 
  isUser = false, 
  sources = [], 
  processingTime,
  contextUsed,
  timestamp,
  isLoading = false 
}) {
  const formatTime = (time) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(new Date(time))
  }

  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex space-x-4 mb-6"
      >
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 1H5C3.89 1 3 1.89 3 3V19C3 20.1 3.9 21 5 21H11V19H5V3H13V9H21Z" />
            </svg>
          </div>
        </div>
        <div className="flex-1 space-y-2">
          <div className="bg-secondary-100 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              <span className="text-sm text-secondary-600 ml-2">Analyzing your question...</span>
            </div>
          </div>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex space-x-4 mb-6 ${isUser ? 'justify-end' : ''}`}
    >
      {!isUser && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 1H5C3.89 1 3 1.89 3 3V19C3 20.1 3.9 21 5 21H11V19H5V3H13V9H21Z" />
            </svg>
          </div>
        </div>
      )}
      
      <div className={`flex-1 space-y-2 ${isUser ? 'max-w-xs' : 'max-w-3xl'}`}>
        <div className={`rounded-lg p-4 ${
          isUser 
            ? 'bg-primary-600 text-white ml-auto' 
            : 'bg-white border border-secondary-200 shadow-sm'
        }`}>
          {isUser ? (
            <p className="text-sm">{message}</p>
          ) : (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={oneDark}
                        language={match[1]}
                        PreTag="div"
                        className="rounded-md"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className="bg-secondary-100 px-1 py-0.5 rounded text-xs" {...props}>
                        {children}
                      </code>
                    )
                  }
                }}
              >
                {message}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Metadata for AI responses */}
        {!isUser && (
          <div className="flex items-center justify-between text-xs text-secondary-500">
            <div className="flex items-center space-x-4">
              {timestamp && (
                <div className="flex items-center space-x-1">
                  <ClockIcon className="h-3 w-3" />
                  <span>{formatTime(timestamp)}</span>
                </div>
              )}
              {processingTime && (
                <div className="flex items-center space-x-1">
                  <CheckCircleIcon className="h-3 w-3" />
                  <span>{processingTime}s</span>
                </div>
              )}
              {contextUsed && (
                <div className="flex items-center space-x-1">
                  <DocumentIcon className="h-3 w-3" />
                  <span>{contextUsed} sources</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Sources */}
        {sources && sources.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            transition={{ delay: 0.3 }}
            className="mt-3"
          >
            <details className="group">
              <summary className="cursor-pointer text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center space-x-2">
                <span>Sources ({sources.length})</span>
                <svg className="w-4 h-4 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </summary>
              <div className="mt-2 space-y-2">
                {sources.map((source, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 * index }}
                    className="flex items-center space-x-2 p-2 bg-secondary-50 rounded-md border border-secondary-200"
                  >
                    <DocumentIcon className="h-4 w-4 text-secondary-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-secondary-900 truncate">
                        {source.document}
                      </p>
                      <p className="text-xs text-secondary-500">
                        Page {source.page_number}
                        {source.relevance && (
                          <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                            {source.relevance}
                          </span>
                        )}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </details>
          </motion.div>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-secondary-300 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-secondary-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
          </div>
        </div>
      )}
    </motion.div>
  )
}
