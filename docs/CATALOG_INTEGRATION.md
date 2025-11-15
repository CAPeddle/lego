# Catalog Integration Architecture

## Overview

The LEGO Inventory Service uses a modular architecture for integrating with external LEGO parts catalogs (Bricklink, Rebrickable, etc.). This design allows swapping catalog providers without changing business logic.

## Architecture

### Three-Layer Design

```
┌─────────────────────────────────────────────┐
│ Business Logic (app/core/services.py)      │
│ - InventoryService uses CatalogServiceInterface │
└─────────────────┬───────────────────────────┘
                  │ depends on interface
┌─────────────────▼───────────────────────────┐
│ Catalog Interface (app/core/catalog_interface.py) │
│ - Abstract contract for any catalog service │
│ - SetSearchResult, SetMetadata, InventoryPart │
└─────────────────┬───────────────────────────┘
                  │ implemented by
┌─────────────────▼───────────────────────────┐
│ Bricklink Implementation                    │
│ (app/infrastructure/bricklink_catalog.py)   │
│ - Uses OAuth client for authentication     │
│ - Implements caching and error handling     │
└─────────────────┬───────────────────────────┘
                  │ depends on
┌─────────────────▼───────────────────────────┐
│ OAuth 1.0a Client                           │
│ (app/infrastructure/oauth_client.py)        │
│ - Generic OAuth client (reusable)          │
│ - Not Bricklink-specific                    │
└─────────────────────────────────────────────┘
```

## Key Components

### 1. Catalog Service Interface (`app/core/catalog_interface.py`)

Defines the contract that any catalog service must implement:

```python
class CatalogServiceInterface(ABC):
    async def search_sets(query: str) -> List[SetSearchResult]
    async def fetch_set_metadata(set_no: str) -> SetMetadata
    async def fetch_set_inventory(set_no: str) -> List[InventoryPart]
    async def health_check() -> bool
```

**Benefits:**
- Allows swapping Bricklink for other services (Rebrickable, BrickOwl, LDraw)
- Makes business logic testable with mocks
- Enforces consistent interface across implementations

### 2. OAuth Client (`app/infrastructure/oauth_client.py`)

Generic OAuth 1.0a HTTP client that can be used with any OAuth 1.0a API:

**Features:**
- OAuth signature generation (handled by `requests-oauthlib`)
- Automatic retries with exponential backoff
- Async support (runs blocking requests in thread pool)
- Configurable timeouts

**Usage:**
```python
config = OAuthConfig(consumer_key, consumer_secret, token, token_secret)
client = OAuthHTTPClient(config)
data = await client.get("https://api.example.com/endpoint")
```

### 3. Bricklink Catalog Service (`app/infrastructure/bricklink_catalog.py`)

Bricklink-specific implementation of `CatalogServiceInterface`:

**Features:**
- OAuth 1.0a authentication via injected OAuth client
- Response caching (24h for metadata, 7d for inventory)
- Comprehensive error handling
- Automatic retry logic
- Pagination support for large inventories

**Endpoints Used:**
- `GET /items/SET/{set_no}` - Set metadata
- `GET /items/SET/{set_no}/subsets` - Parts inventory
- Pagination via `break_minifigs` and `break_subsets` params

### 4. Exception Hierarchy (`app/core/exceptions.py`)

Custom exceptions for catalog operations:

```
LegoServiceError (base)
└── CatalogServiceError
    ├── CatalogAPIError (generic API errors)
    ├── CatalogAuthError (401/403 errors)
    ├── CatalogNotFoundError (404 errors)
    ├── CatalogRateLimitError (429 errors)
    └── CatalogTimeoutError (timeout errors)
```

These exceptions are converted to appropriate HTTP status codes in the API layer.

## Data Flow

### Adding a Set

```
1. User: POST /sets/ {"set_no": "75192"}
                ↓
2. API Router (sets_router.py)
                ↓
3. InventoryService.add_set("75192")
                ↓
4. catalog_service.fetch_set_metadata("75192")
                ↓
5. OAuth Client → Bricklink API
                ↓ (response cached)
6. catalog_service.fetch_set_inventory("75192")
                ↓
7. OAuth Client → Bricklink API
                ↓ (response cached)
8. Store set + parts in database
                ↓
9. Return LegoSet to user
```

## Configuration

### Environment Variables

```bash
# Required for Bricklink integration
LEGO_BRICKLINK_CONSUMER_KEY=your_consumer_key
LEGO_BRICKLINK_CONSUMER_SECRET=your_consumer_secret
LEGO_BRICKLINK_TOKEN=your_token
LEGO_BRICKLINK_TOKEN_SECRET=your_token_secret

# Optional
LEGO_BRICKLINK_CACHE_TTL=86400  # 24 hours (default)
```

Get credentials from: https://www.bricklink.com/v2/api/register_consumer.page

## Testing

### Unit Tests

**OAuth Client** (`tests/test_infrastructure/test_oauth_client.py`):
- 16 tests covering configuration, requests, retries, error handling
- All HTTP calls are mocked

**Bricklink Catalog** (`tests/test_infrastructure/test_bricklink_catalog.py`):
- 14 tests covering metadata fetch, inventory fetch, caching, errors
- OAuth client is mocked

**Run tests:**
```bash
pytest tests/test_infrastructure/ -v
```

### Integration Testing

To test with real Bricklink API:
1. Set environment variables with real credentials
2. Create integration test that makes real API calls
3. Use a known set (e.g., "75192") for testing

**Note:** Bricklink has rate limits (5000 requests/day), so use caching!

## Adding a New Catalog Service

To add support for another catalog (e.g., Rebrickable):

1. **Create implementation:**
   ```python
   # app/infrastructure/rebrickable_catalog.py
   class RebrickableCatalogService(CatalogServiceInterface):
       async def fetch_set_metadata(self, set_no: str) -> SetMetadata:
           # Rebrickable-specific implementation
           pass
   ```

2. **Update dependency injection:**
   ```python
   # app/api/sets_router.py
   catalog_service = RebrickableCatalogService(http_client)
   ```

3. **Business logic unchanged:**
   - `InventoryService` works with any `CatalogServiceInterface`
   - No changes needed to service layer

## Future Enhancements

1. **Search Endpoint**: Add `POST /sets/search` to search by name/description
2. **Catalog Selection**: Allow users to choose catalog provider via config
3. **Hybrid Approach**: Try multiple catalogs if one fails
4. **Background Refresh**: Periodically refresh cached data
5. **Rate Limit Tracking**: Track daily API usage and warn before limit

## Notes

- OAuth module is completely reusable for other OAuth 1.0a APIs
- Caching significantly reduces Bricklink API calls (respects rate limits)
- All catalog operations are async-compatible
- Error handling converts domain exceptions to HTTP exceptions in API layer

---

**Related Files:**
- `app/core/catalog_interface.py` - Interface definition
- `app/core/exceptions.py` - Exception hierarchy
- `app/infrastructure/oauth_client.py` - OAuth client
- `app/infrastructure/bricklink_catalog.py` - Bricklink implementation
- `tests/test_infrastructure/` - Unit tests
