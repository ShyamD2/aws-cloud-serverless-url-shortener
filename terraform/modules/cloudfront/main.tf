# ==============================================================================
# Amazon CloudFront Module (Frontend Static SPA Edge Delivery)
# ==============================================================================

# Origin Access Control (OAC) for modern, secure S3 origin access
resource "aws_cloudfront_origin_access_control" "frontend_oac" {
  name                              = "${var.environment}-frontend-oac"
  description                       = "Origin Access Control for frontend S3 static bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.environment} URL Shortener Frontend Distribution"
  default_root_object = "index.html"
  price_class         = "PriceClass_100" # Lowest cost tier

  origin {
    domain_name              = var.frontend_bucket_regional_domain_name
    origin_id                = "S3-${var.frontend_bucket_id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend_oac.id
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${var.frontend_bucket_id}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  # SPA Routing: Redirect 404 to index.html with 200 OK
  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true # Free SSL/TLS without custom ACM cert
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-frontend-cdn"
  })
}

# Bucket Policy allowing CloudFront OAC to read frontend assets
resource "aws_s3_bucket_policy" "frontend_bucket_policy" {
  bucket = var.frontend_bucket_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipalReadOnly"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${var.frontend_bucket_arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
      }
    ]
  })
}
