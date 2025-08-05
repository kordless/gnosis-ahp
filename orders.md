# ORDERS: AHP Endpoint Restructure

## IMMEDIATE DIRECTIVE

The AHP server endpoint structure is being modified. The `/?f=` pattern is deprecated. Tools are now first-class URL paths.

## NEW STRUCTURE

### Authentication
- **OLD**: `/?f=auth&token={key}`
- **NEW**: `/auth?token={key}`

### Schema Discovery  
- **OLD**: `/?f=openapi`
- **NEW**: `/openapi` (or just `/schema`)

### Tool Execution
- **OLD**: `/?f=tool&name={tool_name}&bearer_token={token}&param1=value1`
- **NEW**: `/{tool_name}?bearer_token={token}&param1=value1`

## IMPLEMENTATION STEPS

1. **Update the main request handler** in the AHP server to route based on path instead of the `f` parameter
2. **Each tool becomes its own route**: 
   - `/generate_qr_code?data=hello&bearer_token={token}`
   - `/echo?text=test&bearer_token={token}`
3. **Reserved routes** that cannot be tool names: `/auth`, `/openapi`, `/schema`, `/health`
4. **Backward compatibility** (optional): Keep `/?f=` working during transition

## BENEFITS
- Cleaner URLs
- RESTful design  
- Each tool owns its parameter namespace
- Better for API documentation
- More intuitive for developers

## DEPLOY
Make it so. The tools deserve to be resources, not just functions.

Trek has spoken.