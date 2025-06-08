from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from src.database.models import MovieModel
from src.database.session import get_db as get_async_session
from src.schemas.movies import MovieDetailResponseSchema, MovieListResponseSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        session: AsyncSession = Depends(get_async_session),
):
    offset = (page - 1) * per_page

    total_stmt = select(func.count()).select_from(MovieModel)
    total_result = await session.execute(total_stmt)
    total_items = total_result.scalar_one()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    query = select(MovieModel).offset(offset).limit(per_page)
    result = await session.execute(query)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_path = str(request.url.path)

    total_pages = (total_items + per_page - 1) // per_page

    def make_url(p):
        return f"{base_path}?page={p}&per_page={per_page}"

    return {
        "movies": [MovieDetailResponseSchema.from_orm(movie) for movie in movies],
        "prev_page": make_url(page - 1) if page > 1 else None,
        "next_page": make_url(page + 1) if page < total_pages else None,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_by_id(
        movie_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie
