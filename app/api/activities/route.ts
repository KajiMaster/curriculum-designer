import { NextResponse } from 'next/server'
import { db } from '@/lib/db'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    
    const activity = await db.activity.create({
      data: {
        title: body.title,
        description: body.description,
        category: body.category,
        difficulty: body.difficulty,
        minDuration: body.minDuration || body.typicalDuration - 5,
        maxDuration: body.maxDuration || body.typicalDuration + 10,
        typicalDuration: body.typicalDuration,
        objectives: body.objectives,
        instructions: body.instructions,
        materials: body.materials || {},
        variations: {},
        tags: body.tags || [],
        profession: body.profession || [],
        createdById: 'temp-user-id', // TODO: Replace with actual user ID from auth
        isPublic: false
      }
    })

    return NextResponse.json(activity)
  } catch (error) {
    console.error('Error creating activity:', error)
    return NextResponse.json(
      { error: 'Failed to create activity' },
      { status: 500 }
    )
  }
}

export async function GET() {
  try {
    const activities = await db.activity.findMany({
      where: {
        isArchived: false
      },
      orderBy: {
        createdAt: 'desc'
      },
      include: {
        createdBy: {
          select: {
            name: true,
            email: true
          }
        },
        metrics: true
      }
    })

    return NextResponse.json(activities)
  } catch (error) {
    console.error('Error fetching activities:', error)
    return NextResponse.json(
      { error: 'Failed to fetch activities' },
      { status: 500 }
    )
  }
}