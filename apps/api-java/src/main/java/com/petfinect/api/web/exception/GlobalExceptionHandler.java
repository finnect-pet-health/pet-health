package com.petfinect.api.web.exception;

import java.util.stream.Collectors;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 전역 예외 핸들러 — 도메인 예외를 RFC 9457 ProblemDetail JSON 으로 변환.
 *
 * <h3>{@code @RestControllerAdvice}</h3>
 * <ul>
 *   <li>{@code @ControllerAdvice} + {@code @ResponseBody} — 모든 컨트롤러에 cross-cutting 적용.</li>
 *   <li>예외 타입별 {@code @ExceptionHandler} 메서드가 매칭되어 변환.</li>
 *   <li>Python FastAPI 의 exception handler 등록과 동일 자리.</li>
 * </ul>
 *
 * <h3>응답 schema (Python {@code http_error} 와 정렬)</h3>
 * <pre>{@code
 * {
 *   "type": "about:blank",
 *   "title": "...",
 *   "status": 401,
 *   "detail": "...",
 *   "code": "UNAUTHORIZED"
 * }
 * }</pre>
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

	@ExceptionHandler(ApiException.class)
	public ResponseEntity<ProblemDetail> handleApi(ApiException exc) {
		ProblemDetail pd = ProblemDetail.forStatusAndDetail(exc.status(), exc.getMessage());
		pd.setProperty("code", exc.errorCode());
		return ResponseEntity.status(exc.status()).body(pd);
	}

	@ExceptionHandler(MethodArgumentNotValidException.class)
	public ResponseEntity<ProblemDetail> handleValidation(MethodArgumentNotValidException exc) {
		String detail = exc.getBindingResult().getFieldErrors().stream()
			.map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
			.collect(Collectors.joining(", "));
		ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, detail);
		pd.setProperty("code", "VALIDATION_FAILED");
		return ResponseEntity.badRequest().body(pd);
	}
}
