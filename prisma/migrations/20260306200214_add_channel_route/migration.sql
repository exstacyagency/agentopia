-- CreateTable
CREATE TABLE "UsageEvent" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "domain" TEXT NOT NULL,
    "jobId" TEXT,
    "jobType" TEXT,
    "modelUsed" TEXT,
    "deltaCredits" DOUBLE PRECISION NOT NULL,
    "balanceAfter" DOUBLE PRECISION NOT NULL,
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "UsageEvent_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CreditReservation" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "jobId" TEXT NOT NULL,
    "jobType" TEXT NOT NULL,
    "domain" TEXT NOT NULL,
    "estimatedCredits" DOUBLE PRECISION NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'ACTIVE',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "resolvedAt" TIMESTAMP(3),

    CONSTRAINT "CreditReservation_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SpendCap" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "domain" TEXT NOT NULL,
    "dailyLimit" DOUBLE PRECISION,
    "monthlyLimit" DOUBLE PRECISION,
    "subscriptionLimit" DOUBLE PRECISION,
    "enabled" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "SpendCap_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "UserSubscription" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "tier" TEXT NOT NULL,
    "domain" TEXT NOT NULL,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "billingAnchorDay" INTEGER NOT NULL DEFAULT 1,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "UserSubscription_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ContainerRecord" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "host" TEXT NOT NULL,
    "port" INTEGER NOT NULL,
    "gatewayToken" TEXT NOT NULL,
    "openclawVersion" TEXT NOT NULL,
    "configVersion" INTEGER NOT NULL,
    "lastHeartbeatAt" TIMESTAMP(3),
    "missedHeartbeats" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ContainerRecord_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "MemoryRecord" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "domain" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "importance" DOUBLE PRECISION NOT NULL,
    "embedding" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "lastAccessedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "pinned" BOOLEAN NOT NULL DEFAULT false,
    "archived" BOOLEAN NOT NULL DEFAULT false,
    "source" TEXT NOT NULL,
    "supersededBy" TEXT,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "MemoryRecord_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "MemoryEdge" (
    "id" TEXT NOT NULL,
    "fromId" TEXT NOT NULL,
    "toId" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "MemoryEdge_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ChannelRoute" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "containerId" TEXT NOT NULL,
    "platform" TEXT NOT NULL,
    "platformUserId" TEXT NOT NULL,
    "platformChannelId" TEXT NOT NULL,
    "gatewayPort" INTEGER NOT NULL,
    "gatewayToken" TEXT NOT NULL,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "lastMessageAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ChannelRoute_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "UsageEvent_userId_domain_idx" ON "UsageEvent"("userId", "domain");

-- CreateIndex
CREATE INDEX "UsageEvent_userId_createdAt_idx" ON "UsageEvent"("userId", "createdAt");

-- CreateIndex
CREATE INDEX "CreditReservation_userId_status_idx" ON "CreditReservation"("userId", "status");

-- CreateIndex
CREATE INDEX "CreditReservation_jobId_idx" ON "CreditReservation"("jobId");

-- CreateIndex
CREATE INDEX "SpendCap_userId_idx" ON "SpendCap"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "SpendCap_userId_domain_key" ON "SpendCap"("userId", "domain");

-- CreateIndex
CREATE INDEX "UserSubscription_userId_active_idx" ON "UserSubscription"("userId", "active");

-- CreateIndex
CREATE UNIQUE INDEX "ContainerRecord_port_key" ON "ContainerRecord"("port");

-- CreateIndex
CREATE INDEX "ContainerRecord_userId_status_idx" ON "ContainerRecord"("userId", "status");

-- CreateIndex
CREATE INDEX "ContainerRecord_status_lastHeartbeatAt_idx" ON "ContainerRecord"("status", "lastHeartbeatAt");

-- CreateIndex
CREATE INDEX "MemoryRecord_userId_archived_pinned_idx" ON "MemoryRecord"("userId", "archived", "pinned");

-- CreateIndex
CREATE INDEX "MemoryRecord_userId_domain_type_idx" ON "MemoryRecord"("userId", "domain", "type");

-- CreateIndex
CREATE INDEX "MemoryRecord_lastAccessedAt_idx" ON "MemoryRecord"("lastAccessedAt");

-- CreateIndex
CREATE INDEX "MemoryEdge_fromId_idx" ON "MemoryEdge"("fromId");

-- CreateIndex
CREATE INDEX "MemoryEdge_toId_idx" ON "MemoryEdge"("toId");

-- CreateIndex
CREATE INDEX "MemoryEdge_type_idx" ON "MemoryEdge"("type");

-- CreateIndex
CREATE INDEX "ChannelRoute_userId_idx" ON "ChannelRoute"("userId");

-- CreateIndex
CREATE INDEX "ChannelRoute_platform_platformUserId_idx" ON "ChannelRoute"("platform", "platformUserId");

-- CreateIndex
CREATE INDEX "ChannelRoute_active_idx" ON "ChannelRoute"("active");
