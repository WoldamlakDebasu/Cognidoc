import { Fragment } from 'react'
import { Transition } from '@headlessui/react'
import { CheckCircleIcon, ExclamationTriangleIcon, XCircleIcon, InformationCircleIcon } from '@heroicons/react/24/outline'
import { XMarkIcon } from '@heroicons/react/20/solid'

const icons = {
  success: CheckCircleIcon,
  warning: ExclamationTriangleIcon,
  error: XCircleIcon,
  info: InformationCircleIcon,
}

const colorClasses = {
  success: {
    bg: 'bg-success-50',
    border: 'border-success-200',
    icon: 'text-success-400',
    title: 'text-success-800',
    message: 'text-success-700',
    button: 'bg-success-50 text-success-500 hover:bg-success-100 focus:ring-success-600',
  },
  warning: {
    bg: 'bg-warning-50',
    border: 'border-warning-200',
    icon: 'text-warning-400',
    title: 'text-warning-800',
    message: 'text-warning-700',
    button: 'bg-warning-50 text-warning-500 hover:bg-warning-100 focus:ring-warning-600',
  },
  error: {
    bg: 'bg-danger-50',
    border: 'border-danger-200',
    icon: 'text-danger-400',
    title: 'text-danger-800',
    message: 'text-danger-700',
    button: 'bg-danger-50 text-danger-500 hover:bg-danger-100 focus:ring-danger-600',
  },
  info: {
    bg: 'bg-primary-50',
    border: 'border-primary-200',
    icon: 'text-primary-400',
    title: 'text-primary-800',
    message: 'text-primary-700',
    button: 'bg-primary-50 text-primary-500 hover:bg-primary-100 focus:ring-primary-600',
  },
}

export default function Toast({ show, type = 'info', title, message, onClose, autoClose = true }) {
  const Icon = icons[type]
  const colors = colorClasses[type]

  // Auto close after 5 seconds
  if (autoClose && show) {
    setTimeout(() => {
      onClose?.()
    }, 5000)
  }

  return (
    <Transition
      show={show}
      as={Fragment}
      enter="transform ease-out duration-300 transition"
      enterFrom="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
      enterTo="translate-y-0 opacity-100 sm:translate-x-0"
      leave="transition ease-in duration-100"
      leaveFrom="opacity-100"
      leaveTo="opacity-0"
    >
      <div className={`max-w-sm w-full ${colors.bg} ${colors.border} border rounded-lg shadow-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden`}>
        <div className="p-4">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <Icon className={`h-6 w-6 ${colors.icon}`} aria-hidden="true" />
            </div>
            <div className="ml-3 w-0 flex-1 pt-0.5">
              <p className={`text-sm font-medium ${colors.title}`}>{title}</p>
              {message && <p className={`mt-1 text-sm ${colors.message}`}>{message}</p>}
            </div>
            <div className="ml-4 flex-shrink-0 flex">
              <button
                className={`${colors.button} rounded-md inline-flex text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2`}
                onClick={onClose}
              >
                <span className="sr-only">Close</span>
                <XMarkIcon className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  )
}
