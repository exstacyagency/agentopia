-- CreateTable
CREATE TABLE "RunningTurn" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "agentSlot" TEXT NOT NULL,
    "sessionId" TEXT NOT NULL,
    "jobType" TEXT NOT NULL,
    "startedAt" TIMESTAMP(3) NOT NULL,
    "timeoutSeconds" INTEGER NOT NULL,
    "status" TEXT NOT NULL,
    "retryCount" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "RunningTurn_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "RunningTurn_userId_idx" ON "RunningTurn"("userId");

-- CreateIndex
CREATE INDEX "RunningTurn_status_idx" ON "RunningTurn"("status");
