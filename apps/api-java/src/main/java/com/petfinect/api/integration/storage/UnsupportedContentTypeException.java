package com.petfinect.api.integration.storage;

public class UnsupportedContentTypeException extends RuntimeException {
	public UnsupportedContentTypeException(String message) {
		super(message);
	}
}
