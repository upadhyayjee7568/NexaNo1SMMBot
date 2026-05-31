import { pgTable, text, timestamp, boolean, serial, numeric, integer, jsonb } from 'drizzle-orm/pg-core'

// --- Better Auth required tables -------------------------------------------
// Column names are camelCase to match Better Auth's defaults. Do not rename.

export const user = pgTable('user', {
  id: text('id').primaryKey(),
  name: text('name').notNull(),
  email: text('email').notNull().unique(),
  emailVerified: boolean('emailVerified').notNull().default(false),
  image: text('image'),
  createdAt: timestamp('createdAt').notNull().defaultNow(),
  updatedAt: timestamp('updatedAt').notNull().defaultNow(),
})

export const session = pgTable('session', {
  id: text('id').primaryKey(),
  expiresAt: timestamp('expiresAt').notNull(),
  token: text('token').notNull().unique(),
  createdAt: timestamp('createdAt').notNull().defaultNow(),
  updatedAt: timestamp('updatedAt').notNull().defaultNow(),
  ipAddress: text('ipAddress'),
  userAgent: text('userAgent'),
  userId: text('userId')
    .notNull()
    .references(() => user.id, { onDelete: 'cascade' }),
})

export const account = pgTable('account', {
  id: text('id').primaryKey(),
  accountId: text('accountId').notNull(),
  providerId: text('providerId').notNull(),
  userId: text('userId')
    .notNull()
    .references(() => user.id, { onDelete: 'cascade' }),
  accessToken: text('accessToken'),
  refreshToken: text('refreshToken'),
  idToken: text('idToken'),
  accessTokenExpiresAt: timestamp('accessTokenExpiresAt'),
  refreshTokenExpiresAt: timestamp('refreshTokenExpiresAt'),
  scope: text('scope'),
  password: text('password'),
  createdAt: timestamp('createdAt').notNull().defaultNow(),
  updatedAt: timestamp('updatedAt').notNull().defaultNow(),
})

export const verification = pgTable('verification', {
  id: text('id').primaryKey(),
  identifier: text('identifier').notNull(),
  value: text('value').notNull(),
  expiresAt: timestamp('expiresAt').notNull(),
  createdAt: timestamp('createdAt').defaultNow(),
  updatedAt: timestamp('updatedAt').defaultNow(),
})

// --- App tables ------------------------------------------------------------
// Add your app tables below. Always include a plain `userId` column so queries
// can be scoped per user — the security model depends on this column existing,
// not on a foreign key. Do NOT add a foreign key constraint
// (`.references(() => user.id, ...)`) unless the user explicitly asks for
// foreign keys or referential integrity; FK constraints make iterating on the
// schema harder.
//
// Example:
//
// import { serial } from "drizzle-orm/pg-core"
//
// export const todos = pgTable("todos", {
//   id: serial("id").primaryKey(),
//   userId: text("userId").notNull(),
//   title: text("title").notNull(),
//   completed: boolean("completed").notNull().default(false),
//   createdAt: timestamp("createdAt").notNull().defaultNow(),
// })
//
// If the user asks for foreign keys, add the reference back in:
//   userId: text("userId")
//     .notNull()
//     .references(() => user.id, { onDelete: "cascade" }),

// --- SMM Panel Tables ---

export const smmUsers = pgTable('smm_users', {
  id: serial('id').primaryKey(),
  userId: text('userId').notNull(),
  telegramId: numeric('telegram_id'),
  telegramUsername: text('telegram_username'),
  fullName: text('full_name'),
  phone: text('phone'),
  role: text('role').default('user'),
  status: text('status').default('active'),
  walletBalance: numeric('wallet_balance', { precision: 12, scale: 2 }).default('0'),
  totalSpent: numeric('total_spent', { precision: 12, scale: 2 }).default('0'),
  totalOrders: integer('total_orders').default(0),
  referralCode: text('referral_code'),
  apiKey: text('api_key'),
  riskScore: integer('risk_score').default(0),
  isBanned: boolean('is_banned').default(false),
  banReason: text('ban_reason'),
  lastActive: timestamp('last_active'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
})

export const categories = pgTable('categories', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
  slug: text('slug').notNull().unique(),
  description: text('description'),
  icon: text('icon'),
  sortOrder: integer('sort_order').default(0),
  isActive: boolean('is_active').default(true),
  createdAt: timestamp('created_at').notNull().defaultNow(),
})

export const services = pgTable('services', {
  id: serial('id').primaryKey(),
  categoryId: integer('category_id'),
  providerServiceId: text('provider_service_id'),
  name: text('name').notNull(),
  description: text('description'),
  platform: text('platform'),
  type: text('type'),
  rate: numeric('rate', { precision: 12, scale: 4 }).notNull(),
  minQuantity: integer('min_quantity').default(10),
  maxQuantity: integer('max_quantity').default(100000),
  isActive: boolean('is_active').default(true),
  isDripFeed: boolean('is_drip_feed').default(false),
  isRefill: boolean('is_refill').default(false),
  refillDays: integer('refill_days').default(0),
  averageTime: text('average_time'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
})

export const orders = pgTable('orders', {
  id: serial('id').primaryKey(),
  userId: integer('user_id').notNull(),
  serviceId: integer('service_id').notNull(),
  providerOrderId: text('provider_order_id'),
  link: text('link').notNull(),
  quantity: integer('quantity').notNull(),
  charge: numeric('charge', { precision: 12, scale: 2 }).notNull(),
  startCount: integer('start_count'),
  status: text('status').default('pending'),
  remains: integer('remains'),
  currency: text('currency').default('INR'),
  isDripFeed: boolean('is_drip_feed').default(false),
  dripFeedRuns: integer('drip_feed_runs'),
  dripFeedInterval: integer('drip_feed_interval'),
  cancelReason: text('cancel_reason'),
  refundAmount: numeric('refund_amount', { precision: 12, scale: 2 }),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
})

export const transactions = pgTable('transactions', {
  id: serial('id').primaryKey(),
  userId: integer('user_id').notNull(),
  type: text('type').notNull(),
  amount: numeric('amount', { precision: 12, scale: 2 }).notNull(),
  balanceBefore: numeric('balance_before', { precision: 12, scale: 2 }),
  balanceAfter: numeric('balance_after', { precision: 12, scale: 2 }),
  referenceId: text('reference_id'),
  referenceType: text('reference_type'),
  paymentMethod: text('payment_method'),
  paymentId: text('payment_id'),
  status: text('status').default('pending'),
  notes: text('notes'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
})

export const tickets = pgTable('tickets', {
  id: serial('id').primaryKey(),
  userId: integer('user_id').notNull(),
  orderId: integer('order_id'),
  subject: text('subject').notNull(),
  message: text('message').notNull(),
  category: text('category').default('general'),
  priority: text('priority').default('medium'),
  status: text('status').default('open'),
  assignedTo: integer('assigned_to'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
})

export const ticketMessages = pgTable('ticket_messages', {
  id: serial('id').primaryKey(),
  ticketId: integer('ticket_id').notNull(),
  userId: integer('user_id').notNull(),
  message: text('message').notNull(),
  isAdmin: boolean('is_admin').default(false),
  attachments: jsonb('attachments'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
})

export const notifications = pgTable('notifications', {
  id: serial('id').primaryKey(),
  userId: integer('user_id').notNull(),
  title: text('title').notNull(),
  message: text('message').notNull(),
  type: text('type').default('info'),
  isRead: boolean('is_read').default(false),
  data: jsonb('data'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
})

export const botConfig = pgTable('bot_config', {
  id: serial('id').primaryKey(),
  configKey: text('config_key').notNull().unique(),
  configValue: text('config_value'),
  configType: text('config_type').default('string'),
  description: text('description'),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
  updatedBy: integer('updated_by'),
})

export const portalSettings = pgTable('portal_settings', {
  id: serial('id').primaryKey(),
  settingKey: text('setting_key').notNull().unique(),
  settingValue: text('setting_value'),
  settingType: text('setting_type').default('string'),
  description: text('description'),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
  updatedBy: integer('updated_by'),
})
