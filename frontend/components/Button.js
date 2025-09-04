import { forwardRef } from 'react'
import { motion } from 'framer-motion'
import { clsx } from 'clsx'

const variants = {
  primary: 'bg-primary-600 hover:bg-primary-700 focus:ring-primary-500 text-white shadow-sm',
  secondary: 'bg-white hover:bg-secondary-50 focus:ring-primary-500 text-secondary-900 border border-secondary-300 shadow-sm',
  success: 'bg-success-600 hover:bg-success-700 focus:ring-success-500 text-white shadow-sm',
  danger: 'bg-danger-600 hover:bg-danger-700 focus:ring-danger-500 text-white shadow-sm',
  outline: 'border-2 border-primary-600 text-primary-600 hover:bg-primary-50 focus:ring-primary-500',
  ghost: 'text-secondary-600 hover:text-secondary-900 hover:bg-secondary-100 focus:ring-primary-500',
}

const sizes = {
  xs: 'px-2 py-1 text-xs',
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
  xl: 'px-8 py-4 text-lg',
}

const Button = forwardRef(({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  disabled = false,
  loading = false,
  icon,
  iconPosition = 'left',
  animate = true,
  ...props
}, ref) => {
  const Component = animate ? motion.button : 'button'
  
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed'
  
  const classes = clsx(
    baseClasses,
    variants[variant],
    sizes[size],
    className
  )

  const iconClasses = clsx(
    'flex-shrink-0',
    size === 'xs' ? 'h-3 w-3' : size === 'sm' ? 'h-4 w-4' : 'h-5 w-5',
    iconPosition === 'left' ? 'mr-2' : 'ml-2'
  )

  const LoadingSpinner = () => (
    <svg className={clsx(iconClasses, 'animate-spin')} fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
  )

  const content = (
    <>
      {loading && <LoadingSpinner />}
      {!loading && icon && iconPosition === 'left' && (
        <icon.type {...icon.props} className={clsx(iconClasses, icon.props?.className)} />
      )}
      {children}
      {!loading && icon && iconPosition === 'right' && (
        <icon.type {...icon.props} className={clsx(iconClasses, icon.props?.className)} />
      )}
    </>
  )

  return (
    <Component
      ref={ref}
      className={classes}
      disabled={disabled || loading}
      whileHover={animate && !disabled ? { scale: 1.02 } : undefined}
      whileTap={animate && !disabled ? { scale: 0.98 } : undefined}
      transition={{ duration: 0.1 }}
      {...props}
    >
      {content}
    </Component>
  )
})

Button.displayName = 'Button'

export default Button
