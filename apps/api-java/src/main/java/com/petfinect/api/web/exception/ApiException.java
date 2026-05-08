package com.petfinect.api.web.exception;

import org.springframework.http.HttpStatus;

/**
 * 도메인 → HTTP 매핑용 표준 예외.
 *
 * <p>Python {@code app.api.v1._errors.http_error(status, code, detail)} 와 동일 schema 로
 * 응답되도록 {@link GlobalExceptionHandler} 에서 ProblemDetail 형태로 변환.
 */
public class ApiException extends RuntimeException {
	private final HttpStatus status;
	private final String errorCode;

	public ApiException(HttpStatus status, String errorCode, String detail) {
		super(detail);
		this.status = status;
		this.errorCode = errorCode;
	}

	public HttpStatus status() {
		return status;
	}

	public String errorCode() {
		return errorCode;
	}
}
